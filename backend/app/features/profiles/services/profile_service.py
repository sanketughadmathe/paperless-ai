from supabase import Client
from app.features.profiles.schemas.profile import ProfileCreate, ProfileUpdate, Profile
from fastapi import HTTPException, status
import uuid


class ProfileService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_profile(self, user_id: uuid.UUID) -> Profile:
        response = (
            self.supabase.from_("profiles")
            .select("*")
            .eq("id", str(user_id))
            .execute()
        )

        # If profile exists, return it
        if response.data and len(response.data) > 0:
            return Profile(**response.data[0])

        # If no profile exists, create a default one
        try:
            default_profile = ProfileCreate(id=user_id)
            profile = await self.create_profile(default_profile)

            # Also create a personal organization for the user
            await self._create_personal_organization(user_id)

            return profile
        except Exception as e:
            # If creation fails, it might be due to the profile already existing
            # Try to fetch it again
            response = (
                self.supabase.from_("profiles")
                .select("*")
                .eq("id", str(user_id))
                .execute()
            )
            if response.data and len(response.data) > 0:
                return Profile(**response.data[0])

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found and could not be created: {str(e)}"
            )

    async def create_profile(self, profile_data: ProfileCreate) -> Profile:
        response = (
            self.supabase.from_("profiles").insert(profile_data.model_dump(mode='json')).execute()
        )
        if response.data:
            return Profile(**response.data[0])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Profile creation failed."
        )

    async def update_profile(
        self, user_id: uuid.UUID, profile_data: ProfileUpdate
    ) -> Profile:
        # Ensure profile exists first
        await self.get_profile(user_id)

        # Filter out None values to avoid overwriting with nulls
        # Use mode='json' to properly serialize datetime objects to strings
        update_data = {
            k: v
            for k, v in profile_data.model_dump(exclude_unset=True, mode='json').items()
            if v is not None
        }

        response = (
            self.supabase.from_("profiles")
            .update(update_data)
            .eq("id", str(user_id))
            .execute()
        )
        if response.data:
            return Profile(**response.data[0])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Profile update failed."
        )

    async def delete_profile(self, user_id: uuid.UUID):
        response = (
            self.supabase.from_("profiles").delete().eq("id", str(user_id)).execute()
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or already deleted.",
            )
        return {"message": "Profile deleted successfully."}

    async def _create_personal_organization(self, user_id: uuid.UUID):
        """Create a personal organization for the user"""
        try:
            # Get user email for organization setup
            user_response = (
                self.supabase.auth.get_user()
            )

            if not user_response.user:
                return  # Skip org creation if we can't get user info

            user_email = user_response.user.email
            if not user_email:
                return

            # Create personal organization
            org_name = f"{user_email}'s Workspace"
            org_slug = f"personal-{str(user_id)[:8]}"

            org_data = {
                "name": org_name,
                "slug": org_slug,
                "description": "Personal workspace",
                "subscription_tier": "free",
                "subscription_status": "trial",
                "max_users": 1,
                "max_documents": 100,
                "max_storage_bytes": 1073741824  # 1GB
            }

            org_response = (
                self.supabase.from_("organizations")
                .insert(org_data)
                .execute()
            )

            if org_response.data:
                org_id = org_response.data[0]["id"]

                # Get viewer role (default for personal org)
                role_response = (
                    self.supabase.from_("roles")
                    .select("id")
                    .eq("name", "org_owner")  # Give them owner role of their personal org
                    .single()
                    .execute()
                )

                if role_response.data:
                    role_id = role_response.data["id"]

                    # Add user as member
                    member_data = {
                        "organization_id": org_id,
                        "user_id": str(user_id),
                        "role_id": role_id,
                        "is_active": True
                    }

                    self.supabase.from_("organization_members").insert(member_data).execute()

                    # Set as default organization
                    self.supabase.from_("profiles").update({
                        "default_organization_id": org_id
                    }).eq("id", str(user_id)).execute()

        except Exception as e:
            # Don't fail profile creation if org creation fails
            print(f"Warning: Could not create personal organization: {e}")
            pass

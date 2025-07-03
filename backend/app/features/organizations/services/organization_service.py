from supabase import Client
from app.features.organizations.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, AdminOrganizationUpdate, Organization,
    OrganizationMemberCreate, OrganizationMemberUpdate, OrganizationMember,
    OrganizationMemberWithDetails, OrganizationInvitation, OrganizationInvitationResponse,
    Role, Permission, UserOrganizationContext
)
from fastapi import HTTPException, status
import uuid
from typing import List, Optional


class OrganizationService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    # Organization Management
    async def create_organization(self, org_data: OrganizationCreate, owner_user_id: uuid.UUID) -> Organization:
        """Create a new organization and make the user an owner"""
        try:
            # Create organization
            org_response = (
                self.supabase.from_("organizations")
                .insert(org_data.model_dump(mode='json'))
                .execute()
            )

            if not org_response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization creation failed"
                )

            organization = Organization(**org_response.data[0])

            # Get org_owner role
            role_response = (
                self.supabase.from_("roles")
                .select("id")
                .eq("name", "org_owner")
                .single()
                .execute()
            )

            if not role_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="org_owner role not found"
                )

            owner_role_id = role_response.data["id"]

            # Add user as organization owner
            member_data = OrganizationMemberCreate(
                organization_id=organization.id,
                user_id=owner_user_id,
                role_id=uuid.UUID(owner_role_id)
            )

            await self.add_organization_member(member_data)

            return organization

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization creation failed: {str(e)}"
            )

    async def get_organization(self, org_id: uuid.UUID) -> Organization:
        """Get organization by ID"""
        response = (
            self.supabase.from_("organizations")
            .select("*")
            .eq("id", str(org_id))
            .single()
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return Organization(**response.data)

    async def get_user_organizations(self, user_id: uuid.UUID) -> List[Organization]:
        """Get all organizations a user belongs to"""
        response = (
            self.supabase.from_("organizations")
            .select("*")
            .in_("id",
                 self.supabase.from_("organization_members")
                 .select("organization_id")
                 .eq("user_id", str(user_id))
                 .eq("is_active", True)
            )
            .execute()
        )

        return [Organization(**org) for org in response.data or []]

    async def update_organization(self, org_id: uuid.UUID, org_data: OrganizationUpdate) -> Organization:
        """Update organization (for org owners/admins)"""
        update_data = {
            k: v for k, v in org_data.model_dump(exclude_unset=True, mode='json').items()
            if v is not None
        }

        response = (
            self.supabase.from_("organizations")
            .update(update_data)
            .eq("id", str(org_id))
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization update failed"
            )

        return Organization(**response.data[0])

    async def admin_update_organization(self, org_id: uuid.UUID, org_data: AdminOrganizationUpdate) -> Organization:
        """Admin-only organization update with subscription management"""
        update_data = {
            k: v for k, v in org_data.model_dump(exclude_unset=True, mode='json').items()
            if v is not None
        }

        response = (
            self.supabase.from_("organizations")
            .update(update_data)
            .eq("id", str(org_id))
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization update failed"
            )

        return Organization(**response.data[0])

    # Member Management
    async def add_organization_member(self, member_data: OrganizationMemberCreate) -> OrganizationMember:
        """Add a member to an organization"""
        response = (
            self.supabase.from_("organization_members")
            .insert(member_data.model_dump(mode='json'))
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add organization member"
            )

        return OrganizationMember(**response.data[0])

    async def get_organization_members(self, org_id: uuid.UUID) -> List[OrganizationMemberWithDetails]:
        """Get all members of an organization with their details"""
        # Use the user_permissions view for detailed member info
        response = (
            self.supabase.from_("user_permissions")
            .select("*")
            .eq("organization_id", str(org_id))
            .execute()
        )

        members = []
        for row in response.data or []:
            member = OrganizationMemberWithDetails(
                id=uuid.uuid4(),  # This would need to be fetched separately
                organization_id=uuid.UUID(row["organization_id"]),
                user_id=uuid.UUID(row["user_id"]),
                role_id=uuid.uuid4(),  # This would need to be fetched separately
                is_active=True,
                joined_at=None,  # This would need to be fetched separately
                role_name=row["role_name"],
                role_display_name=row["role_display_name"],
                permissions=row["permissions"]
            )
            members.append(member)

        return members

    async def update_member_role(self, member_id: uuid.UUID, member_data: OrganizationMemberUpdate) -> OrganizationMember:
        """Update a member's role or status"""
        update_data = {
            k: v for k, v in member_data.model_dump(exclude_unset=True, mode='json').items()
            if v is not None
        }

        response = (
            self.supabase.from_("organization_members")
            .update(update_data)
            .eq("id", str(member_id))
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update member"
            )

        return OrganizationMember(**response.data[0])

    async def remove_organization_member(self, member_id: uuid.UUID):
        """Remove a member from an organization"""
        response = (
            self.supabase.from_("organization_members")
            .delete()
            .eq("id", str(member_id))
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )

        return {"message": "Member removed successfully"}

    # Role and Permission Management
    async def get_roles(self) -> List[Role]:
        """Get all available roles"""
        response = (
            self.supabase.from_("roles")
            .select("*")
            .execute()
        )

        return [Role(**role) for role in response.data or []]

    async def get_permissions(self) -> List[Permission]:
        """Get all available permissions"""
        response = (
            self.supabase.from_("permissions")
            .select("*")
            .execute()
        )

        return [Permission(**perm) for perm in response.data or []]

    async def check_user_permission(self, user_id: uuid.UUID, org_id: uuid.UUID, permission: str) -> bool:
        """Check if user has specific permission in organization"""
        try:
            # Use the database function
            response = (
                self.supabase.rpc("user_has_permission", {
                    "user_uuid": str(user_id),
                    "org_uuid": str(org_id),
                    "permission_name": permission
                })
                .execute()
            )

            return response.data if response.data is not None else False
        except Exception:
            return False

    async def get_user_permissions(self, user_id: uuid.UUID, org_id: uuid.UUID) -> List[str]:
        """Get all permissions for a user in an organization"""
        response = (
            self.supabase.from_("user_permissions")
            .select("permissions")
            .eq("user_id", str(user_id))
            .eq("organization_id", str(org_id))
            .single()
            .execute()
        )

        if response.data and response.data.get("permissions"):
            return response.data["permissions"]
        return []

    # Organization Context Management
    async def set_current_organization(self, user_id: uuid.UUID, org_id: uuid.UUID):
        """Set user's current organization context"""
        # Upsert the user organization context
        context_data = {
            "user_id": str(user_id),
            "current_organization_id": str(org_id)
        }

        response = (
            self.supabase.from_("user_organization_context")
            .upsert(context_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to set organization context"
            )

        return {"message": "Organization context updated successfully"}

    async def get_current_organization(self, user_id: uuid.UUID) -> Optional[Organization]:
        """Get user's current organization"""
        try:
            # Use the database function
            response = (
                self.supabase.rpc("get_current_organization")
                .execute()
            )

            if response.data:
                org_response = (
                    self.supabase.from_("organizations")
                    .select("*")
                    .eq("id", response.data)
                    .single()
                    .execute()
                )

                if org_response.data:
                    return Organization(**org_response.data)

            return None
        except Exception:
            return None

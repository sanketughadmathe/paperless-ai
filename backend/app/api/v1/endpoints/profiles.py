from fastapi import APIRouter, Depends, status, HTTPException
from supabase import Client
from app.core.supabase_client import get_supabase_client
from app.features.profiles.schemas.profile import ProfileCreate, ProfileUpdate, Profile
from app.features.profiles.services.profile_service import ProfileService
from app.core.dependencies import get_current_active_user, get_authenticated_supabase_client_dep  # Import the new dependency
import uuid

router = APIRouter()


def get_profile_service(
    supabase: Client = Depends(get_authenticated_supabase_client_dep),  # Use authenticated client
) -> ProfileService:
    return ProfileService(supabase)


@router.get("/me", response_model=Profile)
async def read_my_profile(
    current_user: dict = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get the profile of the current authenticated user."""
    user_id = uuid.UUID(current_user["id"])
    return await profile_service.get_profile(user_id)


@router.put("/me", response_model=Profile)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Update the profile of the current authenticated user."""
    user_id = uuid.UUID(current_user["id"])
    return await profile_service.update_profile(user_id, profile_data)


# Note: Profile creation is typically handled automatically on user registration
# via Supabase triggers or a separate internal process.
# For this week, we'll focus on read and update.

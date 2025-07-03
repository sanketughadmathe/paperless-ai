from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client

from app.core.supabase_client import get_supabase_client, get_authenticated_supabase_client
from app.features.auth.services.auth_service import AuthService

# The tokenUrl should point to your login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_auth_service(supabase: Client = Depends(get_supabase_client)) -> AuthService:
    """Dependency to get the AuthService."""
    return AuthService(supabase)


def get_authenticated_supabase_client_dep(token: str = Depends(oauth2_scheme)) -> Client:
    """Dependency to get an authenticated Supabase client."""
    return get_authenticated_supabase_client(token)


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Dependency to get the current authenticated user from a token.
    Raises HTTPException 401 if the user is not valid.
    """
    user = await auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

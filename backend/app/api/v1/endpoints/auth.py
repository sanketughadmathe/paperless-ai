from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from app.core.supabase_client import get_supabase_client
from app.features.auth.schemas.auth import UserCreate, UserLogin, Token
from app.features.auth.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(supabase: Client = Depends(get_supabase_client)) -> AuthService:
    return AuthService(supabase)


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    user = await auth_service.register_user(user_data)
    return {"message": "User registered successfully", "user_id": user.get("id")}


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access token (JSON body)."""
    token = await auth_service.login_user(user_data)
    return token


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth2 compatible token login endpoint.
    Use this endpoint for OAuth2 flows. The username field should contain the email.
    """
    # Create UserLogin object from form data (username will be the email)
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    token = await auth_service.login_user(user_data)
    return token

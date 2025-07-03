from supabase import Client
from app.features.auth.schemas.auth import UserCreate, UserLogin, Token
from fastapi import HTTPException, status


class AuthService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def register_user(self, user_data: UserCreate) -> dict:
        try:
            response = self.supabase.auth.sign_up(
                {"email": user_data.email, "password": user_data.password}
            )
            if response.user:
                return response.user.model_dump()  # Use model_dump() for Pydantic v2
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed.",
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def login_user(self, user_data: UserLogin) -> Token:
        try:
            response = self.supabase.auth.sign_in_with_password(
                {"email": user_data.email, "password": user_data.password}
            )
            if response.session:
                return Token(access_token=response.session.access_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    async def get_current_user(self, token: str) -> dict:
        try:
            # Supabase's auth.get_user() can make a round trip,
            # but for local JWT validation, we can decode it directly.
            # However, for simplicity and relying on Supabase's robust validation,
            # we'll use their method here.
            user_response = self.supabase.auth.get_user(token)
            if user_response.user:
                return user_response.user.model_dump()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

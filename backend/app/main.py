from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client

from app.api.v1.router import api_router  # Import the API router
from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.core.supabase_client import get_supabase_client
from app.features.auth.services.auth_service import AuthService

app = FastAPI(
    title="PaperVault API",
    description="Backend API for PaperVault, an AI-powered document management system.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")  # Include the API router

@app.get("/")
async def read_root():
    return {"message": "Welcome to PaperVault API!"}


@app.get("/healthcheck")
async def healthcheck(supabase: Client = Depends(get_supabase_client)):
    """Check Supabase connection."""
    try:
        response = supabase.from_("profiles").select("id").limit(1).execute()
        if response.data is not None:
            return {
                "status": "ok",
                "supabase_connected": True,
                "data": response.data,
            }
        else:
            return {
                "status": "error",
                "supabase_connected": False,
                "detail": "Supabase data fetch failed",
            }
    except Exception as e:
        return {"status": "error", "supabase_connected": False, "detail": str(e)}


@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current authenticated user's details."""
    return current_user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

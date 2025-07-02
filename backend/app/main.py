from fastapi import Depends, FastAPI
from supabase import Client  # Import Client for type hinting

from .core.config import settings
from .core.supabase_client import get_supabase_client

app = FastAPI(
    title="PaperVault API",
    description="Backend API for PaperVault, an AI-powered document management system.",
    version="0.1.0",
)


@app.get("/")
async def read_root():
    return {"message": "Welcome to PaperVault API!"}


@app.get("/healthcheck")
async def healthcheck(supabase: Client = Depends(get_supabase_client)):
    """Check Supabase connection."""
    try:
        # Attempt a simple query to verify connection
        # This assumes you have a 'profiles' table or similar accessible table
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

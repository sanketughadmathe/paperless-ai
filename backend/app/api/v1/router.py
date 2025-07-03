from fastapi import APIRouter
from app.api.v1.endpoints import auth, profiles, documents, organizations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])

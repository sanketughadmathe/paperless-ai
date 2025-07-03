from fastapi import APIRouter, Depends, status
from app.core.permissions import require_document_view, require_document_create

router = APIRouter()

@router.get("/")
async def get_documents(
    _: dict = Depends(require_document_view)
):
    """Get documents in the current organization context. (Placeholder)"""
    return {"message": "Documents endpoint - Coming soon with organization-scoped access"}


@router.post("/")
async def create_document(
    _: dict = Depends(require_document_create)
):
    """Create a document in the current organization context. (Placeholder)"""
    return {"message": "Document creation endpoint - Coming soon with organization-scoped access"}

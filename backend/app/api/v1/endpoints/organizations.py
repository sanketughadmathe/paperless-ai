from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from typing import List, Optional
import uuid

from app.features.organizations.schemas.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, AdminOrganizationUpdate,
    OrganizationMember, OrganizationMemberCreate, OrganizationMemberUpdate,
    OrganizationMemberWithDetails, Role, Permission
)
from app.features.organizations.services.organization_service import OrganizationService
from app.core.permissions import (
    get_organization_service, require_org_manage, require_user_invite,
    require_user_remove, require_role_assign, require_system_admin,
    get_current_active_user
)

router = APIRouter()


# Organization Management Endpoints
@router.post("/", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Create a new organization. User becomes the organization owner."""
    user_id = uuid.UUID(current_user["id"])
    return await org_service.create_organization(org_data, user_id)


@router.get("/", response_model=List[Organization])
async def get_user_organizations(
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get all organizations the current user belongs to."""
    user_id = uuid.UUID(current_user["id"])
    return await org_service.get_user_organizations(user_id)


@router.get("/{org_id}", response_model=Organization)
async def get_organization(
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get organization details. RLS ensures user can only see orgs they belong to."""
    return await org_service.get_organization(org_id)


@router.put("/{org_id}", response_model=Organization)
async def update_organization(
    org_data: OrganizationUpdate,
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    _: dict = Depends(require_org_manage),  # Permission check
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Update organization. Requires org.manage permission."""
    return await org_service.update_organization(org_id, org_data)


@router.put("/{org_id}/admin", response_model=Organization)
async def admin_update_organization(
    org_data: AdminOrganizationUpdate,
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    _: dict = Depends(require_system_admin),  # System admin only
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Admin-only organization update including subscription management."""
    return await org_service.admin_update_organization(org_id, org_data)


@router.post("/{org_id}/set-current")
async def set_current_organization(
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Set the current organization context for the user."""
    user_id = uuid.UUID(current_user["id"])
    return await org_service.set_current_organization(user_id, org_id)


@router.get("/current/details", response_model=Optional[Organization])
async def get_current_organization(
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get the user's current organization context."""
    user_id = uuid.UUID(current_user["id"])
    return await org_service.get_current_organization(user_id)


# Member Management Endpoints
@router.get("/{org_id}/members", response_model=List[OrganizationMemberWithDetails])
async def get_organization_members(
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get all members of an organization with their roles and permissions."""
    return await org_service.get_organization_members(org_id)


@router.post("/{org_id}/members", response_model=OrganizationMember, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    member_data: OrganizationMemberCreate,
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    _: dict = Depends(require_user_invite),  # Permission check
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Add a member to the organization. Requires user.invite permission."""
    # Ensure the org_id matches the path parameter
    member_data.organization_id = org_id
    return await org_service.add_organization_member(member_data)


@router.put("/{org_id}/members/{member_id}", response_model=OrganizationMember)
async def update_organization_member(
    member_data: OrganizationMemberUpdate,
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    member_id: uuid.UUID = Path(..., description="Member ID"),
    _: dict = Depends(require_role_assign),  # Permission check
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Update a member's role or status. Requires role.assign permission."""
    return await org_service.update_member_role(member_id, member_data)


@router.delete("/{org_id}/members/{member_id}")
async def remove_organization_member(
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    member_id: uuid.UUID = Path(..., description="Member ID"),
    _: dict = Depends(require_user_remove),  # Permission check
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Remove a member from the organization. Requires user.remove permission."""
    return await org_service.remove_organization_member(member_id)


# Role and Permission Endpoints
@router.get("/roles/", response_model=List[Role])
async def get_roles(
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get all available roles in the system."""
    return await org_service.get_roles()


@router.get("/permissions/", response_model=List[Permission])
async def get_permissions(
    category: Optional[str] = Query(None, description="Filter by permission category"),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get all available permissions, optionally filtered by category."""
    permissions = await org_service.get_permissions()

    if category:
        permissions = [p for p in permissions if p.category == category]

    return permissions


@router.get("/{org_id}/my-permissions", response_model=List[str])
async def get_my_permissions(
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get current user's permissions in the specified organization."""
    user_id = uuid.UUID(current_user["id"])
    return await org_service.get_user_permissions(user_id, org_id)

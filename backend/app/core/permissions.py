from functools import wraps
from typing import List, Optional, Union
import uuid
from fastapi import HTTPException, status, Depends
from app.core.dependencies import get_current_active_user, get_authenticated_supabase_client_dep
from app.features.organizations.services.organization_service import OrganizationService


class PermissionChecker:
    """Utility class for checking user permissions"""

    def __init__(self, organization_service: OrganizationService):
        self.org_service = organization_service

    async def check_permission(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        permission: str
    ) -> bool:
        """Check if user has specific permission in organization"""
        return await self.org_service.check_user_permission(user_id, org_id, permission)

    async def check_any_permission(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        permissions: List[str]
    ) -> bool:
        """Check if user has any of the specified permissions"""
        for permission in permissions:
            if await self.check_permission(user_id, org_id, permission):
                return True
        return False

    async def check_all_permissions(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        permissions: List[str]
    ) -> bool:
        """Check if user has all of the specified permissions"""
        for permission in permissions:
            if not await self.check_permission(user_id, org_id, permission):
                return False
        return True


def get_organization_service(supabase = Depends(get_authenticated_supabase_client_dep)) -> OrganizationService:
    """Dependency to get OrganizationService with authenticated client"""
    return OrganizationService(supabase)


def get_permission_checker(org_service: OrganizationService = Depends(get_organization_service)) -> PermissionChecker:
    """Dependency to get PermissionChecker"""
    return PermissionChecker(org_service)


class RequirePermission:
    """Dependency class for requiring specific permissions"""

    def __init__(
        self,
        permissions: Union[str, List[str]],
        require_all: bool = False,
        org_id_param: str = "org_id"
    ):
        self.permissions = permissions if isinstance(permissions, list) else [permissions]
        self.require_all = require_all
        self.org_id_param = org_id_param

    async def __call__(
        self,
        current_user: dict = Depends(get_current_active_user),
        permission_checker: PermissionChecker = Depends(get_permission_checker),
        org_id: Optional[uuid.UUID] = None
    ):
        """Check if current user has required permissions"""
        user_id = uuid.UUID(current_user["id"])

        # If no org_id provided, try to get user's current organization
        if org_id is None:
            current_org = await permission_checker.org_service.get_current_organization(user_id)
            if not current_org:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No organization context available"
                )
            org_id = current_org.id

        # Check permissions
        if self.require_all:
            has_permission = await permission_checker.check_all_permissions(
                user_id, org_id, self.permissions
            )
        else:
            has_permission = await permission_checker.check_any_permission(
                user_id, org_id, self.permissions
            )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission(s): {', '.join(self.permissions)}"
            )

        return {
            "user_id": user_id,
            "org_id": org_id,
            "permissions": self.permissions
        }


class RequireRole:
    """Dependency class for requiring specific roles"""

    def __init__(self, roles: Union[str, List[str]]):
        self.roles = roles if isinstance(roles, list) else [roles]

    async def __call__(
        self,
        current_user: dict = Depends(get_current_active_user),
        org_service: OrganizationService = Depends(get_organization_service)
    ):
        """Check if current user has required role"""
        user_id = uuid.UUID(current_user["id"])

        # Get user's current organization
        current_org = await org_service.get_current_organization(user_id)
        if not current_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No organization context available"
            )

        # Get user's role in current organization
        members = await org_service.get_organization_members(current_org.id)
        user_member = next((m for m in members if m.user_id == user_id), None)

        if not user_member or user_member.role_name not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role(s): {', '.join(self.roles)}"
            )

        return {
            "user_id": user_id,
            "org_id": current_org.id,
            "role": user_member.role_name
        }


# Common permission dependencies
require_document_view = RequirePermission("document.view")
require_document_create = RequirePermission("document.create")
require_document_edit = RequirePermission("document.edit")
require_document_delete = RequirePermission("document.delete")
require_document_manage = RequirePermission("document.manage_all")

require_user_invite = RequirePermission("user.invite")
require_user_remove = RequirePermission("user.remove")
require_role_assign = RequirePermission("role.assign")

require_org_manage = RequirePermission("org.manage")
require_billing_manage = RequirePermission("billing.manage")

# Role-based dependencies
require_org_owner = RequireRole("org_owner")
require_org_admin = RequireRole(["org_owner", "org_admin"])
require_document_manager = RequireRole(["org_owner", "org_admin", "document_manager"])


def require_system_admin(current_user: dict = Depends(get_current_active_user)):
    """Check if user is a system admin (super_admin role)"""
    # This would typically check a system-wide role or flag
    # For now, we'll implement a simple check
    # You could store this in the user's profile or check against specific user IDs

    # Example: Check if user has system admin permission globally
    # In a real implementation, you'd have a system-wide roles table

    user_email = current_user.get("email", "")
    system_admin_emails = [
        # Add system admin emails here
        "admin@yourdomain.com",
        # or check against a database flag
    ]

    if user_email not in system_admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System administrator access required"
        )

    return current_user

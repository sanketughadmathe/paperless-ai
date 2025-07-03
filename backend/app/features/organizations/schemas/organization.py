from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Literal
import uuid
from datetime import datetime

# Define allowed values to match database constraints
SubscriptionTier = Literal["free", "starter", "professional", "enterprise"]
SubscriptionStatus = Literal["trial", "active", "past_due", "cancelled", "expired"]


class OrganizationBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: str
        }
    )

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    billing_email: Optional[str] = None
    subscription_tier: SubscriptionTier = "free"
    subscription_status: SubscriptionStatus = "trial"
    subscription_expires_at: Optional[datetime] = None
    max_users: int = 5
    max_documents: int = 1000
    max_storage_bytes: int = 5368709120  # 5GB
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    """User-editable organization fields (for org owners/admins)"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class AdminOrganizationUpdate(OrganizationBase):
    """Admin-only organization update with subscription management"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    billing_email: Optional[str] = None
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: Optional[SubscriptionStatus] = None
    subscription_expires_at: Optional[datetime] = None
    max_users: Optional[int] = None
    max_documents: Optional[int] = None
    max_storage_bytes: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class Organization(OrganizationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Role Schemas
class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_system_role: bool = True
    permissions: List[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class Role(RoleBase):
    id: uuid.UUID
    created_at: datetime


# Permission Schemas
class Permission(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    created_at: datetime


# Organization Member Schemas
class OrganizationMemberBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    is_active: bool = True


class OrganizationMemberCreate(OrganizationMemberBase):
    pass


class OrganizationMemberUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class OrganizationMember(OrganizationMemberBase):
    id: uuid.UUID
    invited_by: Optional[uuid.UUID] = None
    joined_at: datetime
    invitation_accepted_at: Optional[datetime] = None


class OrganizationMemberWithDetails(OrganizationMember):
    """Extended member info with user and role details"""
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    role_name: str
    role_display_name: str
    permissions: List[str]


# User Organization Context
class UserOrganizationContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    current_organization_id: Optional[uuid.UUID] = None
    updated_at: datetime


# Invitation Schemas
class OrganizationInvitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    role_id: uuid.UUID
    message: Optional[str] = None


class OrganizationInvitationResponse(BaseModel):
    message: str
    invitation_id: Optional[uuid.UUID] = None
    existing_user: bool = False

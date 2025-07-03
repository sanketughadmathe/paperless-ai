from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, Literal
import uuid
from datetime import datetime

# Define the allowed values to match database constraints
SubscriptionTier = Literal["free", "pro", "enterprise"]
SubscriptionStatus = Literal["active", "cancelled", "expired", "trial"]


class ProfileBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: str
        }
    )

    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    billing_info: Optional[Dict[str, Any]] = None
    subscription_tier: SubscriptionTier = "free"
    subscription_status: SubscriptionStatus = "active"
    subscription_expires_at: Optional[datetime] = None
    document_quota: int = 100
    storage_quota_bytes: int = 1073741824  # 1GB default
    usage_stats: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "documents_uploaded": 0,
            "storage_used_bytes": 0,
            "searches_performed": 0,
        }
    )
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    onboarding_completed: bool = False


class ProfileCreate(ProfileBase):
    id: uuid.UUID  # Supabase user ID


class ProfileUpdate(BaseModel):
    """
    User-editable profile fields only.
    Subscription, billing, and usage stats are admin-only.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: str
        }
    )

    # User-editable fields only
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    onboarding_completed: Optional[bool] = None


class AdminProfileUpdate(ProfileBase):
    """
    Admin-only profile update with all fields including subscription management.
    """
    # All fields optional for admin updates
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    billing_info: Optional[Dict[str, Any]] = None
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: Optional[SubscriptionStatus] = None
    subscription_expires_at: Optional[datetime] = None
    document_quota: Optional[int] = None
    storage_quota_bytes: Optional[int] = None
    usage_stats: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    onboarding_completed: Optional[bool] = None


class Profile(ProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

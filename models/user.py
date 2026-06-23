from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    resume_url: Optional[str] = None
    target_role: Optional[str] = None
    interview_timeline: Optional[str] = None
    sessions_used: int = 0
    sessions_limit: int = 3
    plan: str = "free"
    subscription_starts_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    # Computed by API (not stored in DB)
    credits_remaining: Optional[int] = None
    subscription_active: Optional[bool] = None
    subscription_days_left: Optional[int] = None
    can_start_interview: Optional[bool] = None
    access_blocked_reason: Optional[str] = None
    access_message: Optional[str] = None
    plan_label: Optional[str] = None
    is_paid_plan: Optional[bool] = None
    is_owner: Optional[bool] = None
    owner_lifetime_access: Optional[bool] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    target_role: Optional[str] = None
    interview_timeline: Optional[str] = None

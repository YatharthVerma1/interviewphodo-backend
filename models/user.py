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
    sessions_limit: int = 2
    plan: str = "free"
    created_at: Optional[datetime] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    target_role: Optional[str] = None
    interview_timeline: Optional[str] = None

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportResponse(BaseModel):
    id: str
    session_id: str
    overall_score: Optional[int] = None
    phase_scores: Optional[dict] = None
    filler_count: Optional[int] = None
    filler_percentage: Optional[float] = None
    words_per_minute: Optional[float] = None
    pace_verdict: Optional[str] = None
    posture_score: Optional[int] = None
    eye_contact_score: Optional[int] = None
    ai_closing_summary: Optional[str] = None
    created_at: Optional[datetime] = None

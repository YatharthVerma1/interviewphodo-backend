from typing import Optional

from pydantic import BaseModel


class SessionStartRequest(BaseModel):
    company: str
    round_type: str
    difficulty: Optional[str] = None  # "easy" | "medium" | "hard"


class SessionResponse(BaseModel):
    session_id: str
    room_url: str
    company: str
    round_type: str
    status: str
    difficulty: Optional[str] = None


class PostureEventRequest(BaseModel):
    event_type: str
    message: str

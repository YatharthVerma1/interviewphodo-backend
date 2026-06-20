from typing import Optional

from pydantic import BaseModel


class SessionStartRequest(BaseModel):
    company: str
    round_type: str
    # Optional manual override. If omitted, backend auto-derives difficulty from
    # the user's prior completed sessions for this company:
    #   0 prior -> easy   |   1-2 prior -> medium   |   3+ prior -> hard
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

from pydantic import BaseModel


class SessionStartRequest(BaseModel):
    company: str
    round_type: str


class SessionResponse(BaseModel):
    session_id: str
    room_url: str
    company: str
    round_type: str
    status: str


class PostureEventRequest(BaseModel):
    event_type: str
    message: str

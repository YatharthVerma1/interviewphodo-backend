import asyncio
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from routers.auth import get_current_user
from models.session import SessionStartRequest, SessionResponse, PostureEventRequest
from services.daily_service import create_interview_room
from services.interview_fsm import get_session_state
from services.interview_pipeline import run_interview_pipeline
from prompts.companies import VALID_COMPANIES
from database.supabase_client import supabase_admin
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_ROUNDS = ["hr", "technical", "mixed"]


@router.post("/start", response_model=SessionResponse)
async def start_session(
    body: SessionStartRequest,
    current_user: dict = Depends(get_current_user),
):
    company    = body.company.lower().strip()
    round_type = body.round_type.lower().strip()

    if company not in VALID_COMPANIES:
        raise HTTPException(400, f"Invalid company. Valid: {VALID_COMPANIES}")
    if round_type not in VALID_ROUNDS:
        raise HTTPException(400, f"Invalid round_type. Valid: {VALID_ROUNDS}")

    if not settings.daily_configured:
        raise HTTPException(503, "Daily.co is not configured. Set DAILY_API_KEY in .env")
    if not settings.google_configured:
        raise HTTPException(503, "Gemini is not configured. Set GOOGLE_API_KEY in .env")

    # Check session credits
    user = supabase_admin.table("users").select(
        "sessions_used, sessions_limit, resume_text"
    ).eq("id", current_user["id"]).single().execute()

    ud = user.data
    if ud["sessions_used"] >= ud["sessions_limit"]:
        raise HTTPException(
            402,
            "No sessions remaining. Purchase a pack at interviewphodo.com/pricing"
        )

    # Create Daily.co room
    unique_id = uuid.uuid4().hex[:12]
    try:
        room = await create_interview_room(unique_id)
    except Exception as e:
        raise HTTPException(500, f"Room creation failed: {str(e)}")

    # Insert session row
    row = supabase_admin.table("sessions").insert({
        "user_id":         current_user["id"],
        "company":         company,
        "round_type":      round_type,
        "status":          "pending",
        "daily_room_url":  room["url"],
        "daily_room_name": room["name"],
    }).execute()

    session_id = row.data[0]["id"]

    # Deduct one session credit
    supabase_admin.table("users").update({
        "sessions_used": ud["sessions_used"] + 1
    }).eq("id", current_user["id"]).execute()

    # Launch Pipecat pipeline (non-blocking background task)
    asyncio.create_task(run_interview_pipeline(
        room_url    = room["url"],
        room_token  = room["token"],
        session_id  = session_id,
        user_id     = current_user["id"],
        company     = company,
        round_type  = round_type,
        resume_text = ud.get("resume_text") or "",
    ))

    logger.info(f"Session started | {session_id} | {company} | {round_type}")

    return SessionResponse(
        session_id = session_id,
        room_url   = room["url"],
        company    = company,
        round_type = round_type,
        status     = "pending",
    )


@router.get("/{session_id}/status")
async def session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Frontend polls this to update the phase progress bar."""
    state = get_session_state(session_id)
    if state:
        return {
            "session_id":    session_id,
            "status":        "active",
            "current_phase": state.current_phase.value,
            "phase_turn":    state.phase_turn,
            "total_turns":   state.total_turns,
            "filler_count":  state.filler_count,
            "duration_sec":  state.get_duration_seconds(),
        }

    row = supabase_admin.table("sessions").select("*").eq(
        "id", session_id
    ).eq("user_id", current_user["id"]).single().execute()

    if not row.data:
        raise HTTPException(404, "Session not found")
    return row.data


@router.post("/{session_id}/posture-event")
async def posture_event(
    session_id: str,
    body: PostureEventRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Frontend sends posture alerts from MediaPipe (browser-side detection).
    Stored in FSM state and included in the final report.
    """
    state = get_session_state(session_id)
    if not state:
        return {"status": "session_not_active"}
    if state.user_id != current_user["id"]:
        raise HTTPException(403, "Not your session")

    state.add_posture_event(body.event_type, body.message)
    return {"status": "recorded", "total_posture_events": len(state.posture_events)}


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Student clicks 'End Interview' button on frontend."""
    row = supabase_admin.table("sessions").select("user_id").eq(
        "id", session_id
    ).single().execute()

    if not row.data or row.data["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized")

    supabase_admin.table("sessions").update({
        "status": "abandoned", "ended_at": "now()"
    }).eq("id", session_id).execute()

    return {"status": "ended", "session_id": session_id}


@router.get("/my-sessions")
async def my_sessions(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
):
    rows = supabase_admin.table("sessions").select(
        "id, company, round_type, status, current_phase, "
        "total_turns, duration_seconds, started_at, ended_at"
    ).eq("user_id", current_user["id"]).order(
        "created_at", desc=True
    ).limit(limit).execute()
    return rows.data

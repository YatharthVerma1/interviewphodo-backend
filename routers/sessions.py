import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from routers.auth import get_current_user
from models.session import SessionStartRequest, SessionResponse, PostureEventRequest
from services.daily_service import create_interview_room
from services.interview_pipeline import request_pipeline_shutdown, run_interview_pipeline
from services.interview_fsm import get_session_state
from prompts.companies import VALID_COMPANIES
from database.supabase_client import fetch_one, supabase_admin
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Round types a student can pick — each maps to a real Indian placement round:
#   technical     → Round 2-3 (Technical interviews — DSA + Core CS + project deep-dive)
#   managerial    → Round 5 (Managerial — situational, leadership, fitment)
#   hr            → Round 6 (HR — salary, career, traps, background verification)
#   full          → All-in-one practice across every phase
#   coaching      → Coaching mode — AI teaches HOW to answer, not just evaluates
#   multi_persona → Panel-style — different interviewer per phase
# "mixed" kept as a backward-compat alias for "full".
VALID_ROUNDS = [
    "technical", "managerial", "hr", "full",
    "coaching", "multi_persona", "mixed",
]
VALID_DIFFICULTIES = ("easy", "medium", "hard")


_ROUND_OPTIONS_FOR_FRONTEND = [
    {"round": "coaching",      "label": "Coaching",        "tagline": "AI teaches you the frameworks. Best for first-timers."},
    {"round": "technical",     "label": "Technical (R2-3)","tagline": "DSA + Core CS + project deep-dive."},
    {"round": "managerial",    "label": "Managerial (R5)", "tagline": "Situational, leadership, project ownership."},
    {"round": "hr",            "label": "HR (R6)",         "tagline": "Salary, career, India-specific traps."},
    {"round": "multi_persona", "label": "Panel",           "tagline": "Different interviewer per phase, like a real placement panel."},
    {"round": "full",          "label": "Full mock",       "tagline": "Every phase, longest format. Realistic end-to-end."},
]


def _company_completed_count(user_id: str, company: str) -> int:
    rows = supabase_admin.table("sessions").select("id").eq(
        "user_id", user_id
    ).eq("company", company).eq("status", "completed").execute()
    return len(rows.data or [])


@router.post("/start", response_model=SessionResponse)
async def start_session(
    body: SessionStartRequest,
    current_user: dict = Depends(get_current_user),
):
    company    = body.company.lower().strip()
    round_type = body.round_type.lower().strip()
    difficulty = (body.difficulty or "").lower().strip() or None

    if company not in VALID_COMPANIES:
        raise HTTPException(400, f"Invalid company. Valid: {VALID_COMPANIES}")
    if round_type not in VALID_ROUNDS:
        raise HTTPException(400, f"Invalid round_type. Valid: {VALID_ROUNDS}")
    if difficulty is not None and difficulty not in VALID_DIFFICULTIES:
        raise HTTPException(
            400,
            f"Invalid difficulty. Valid: {list(VALID_DIFFICULTIES)} (or omit for auto)",
        )

    if not settings.daily_configured:
        raise HTTPException(503, "Daily.co is not configured. Set DAILY_API_KEY in .env")
    if not settings.google_configured:
        raise HTTPException(503, "Gemini is not configured. Set GOOGLE_API_KEY in .env")

    # Check session credits (CHECK only — actual deduction happens in
    # interview_pipeline.on_first_participant_joined so users who never
    # join their session are not charged).
    ud = fetch_one(
        supabase_admin.table("users")
        .select("sessions_used, sessions_limit, resume_text")
        .eq("id", current_user["id"])
    )
    if not ud:
        raise HTTPException(404, "User profile not found")
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

    # Launch Pipecat pipeline (non-blocking background task)
    asyncio.create_task(run_interview_pipeline(
        room_url            = room["url"],
        room_token          = room["token"],
        session_id          = session_id,
        user_id             = current_user["id"],
        company             = company,
        round_type          = round_type,
        resume_text         = ud.get("resume_text") or "",
        difficulty_override = difficulty,
    ))

    logger.info(
        f"Session started | {session_id} | {company} | {round_type} | "
        f"difficulty={difficulty or 'auto'}"
    )

    return SessionResponse(
        session_id = session_id,
        room_url   = room["student_url"],
        company    = company,
        round_type = round_type,
        status     = "pending",
        difficulty = difficulty,
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

    row = fetch_one(
        supabase_admin.table("sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", current_user["id"])
    )
    if not row:
        raise HTTPException(404, "Session not found")
    return row


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
    row = fetch_one(
        supabase_admin.table("sessions").select("user_id").eq("id", session_id)
    )
    if not row:
        raise HTTPException(404, "Session not found")
    if row["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized")

    await request_pipeline_shutdown(session_id, reason="manual_end")

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


@router.get("/next-recommended")
async def next_recommended(
    company: Optional[str] = Query(
        None,
        description="If provided, recommends the next round for this specific company. "
                    "If omitted, picks the company you've used least.",
    ),
    current_user: dict = Depends(get_current_user),
):
    """Curriculum endpoint — tells the frontend which round to suggest next.

    Recommendation logic per company:
      0 prior completed sessions  → coaching      (learn the frameworks first)
      1-3 prior completed         → technical / managerial / hr / full
                                      (auto-difficulty handles rising challenge)
      4+ prior completed          → multi_persona (panel-style finale)

    The user can always override the recommendation when calling /start.
    """
    user_id = current_user["id"]

    if company:
        company = company.lower().strip()
        if company not in VALID_COMPANIES:
            raise HTTPException(400, f"Invalid company. Valid: {VALID_COMPANIES}")
        target_company = company
    else:
        # Pick the company the user has practised LEAST. Frontend can show
        # "Branch out — try TCS next" suggestions this way.
        per_company_counts = {c: _company_completed_count(user_id, c)
                              for c in VALID_COMPANIES}
        target_company = min(per_company_counts, key=per_company_counts.get)

    n_done = _company_completed_count(user_id, target_company)

    if n_done == 0:
        rec_round = "coaching"
        reason = (
            f"This is your first session for {target_company}. "
            f"Coaching mode trains you on every question type — frameworks for "
            f"behavioral, structure for technical, strategy for HR — before you "
            f"face a real mock interview."
        )
    elif n_done < 4:
        # Pick a normal round the user hasn't tried yet for this company,
        # otherwise default to 'full'.
        rows = supabase_admin.table("sessions").select("round_type").eq(
            "user_id", user_id
        ).eq("company", target_company).eq("status", "completed").execute()
        tried = {r["round_type"] for r in (rows.data or [])}
        for candidate in ("technical", "managerial", "hr", "full"):
            if candidate not in tried:
                rec_round = candidate
                break
        else:
            rec_round = "full"
        reason = (
            f"You've completed {n_done} session(s) for {target_company}. "
            f"This is a regular mock with auto-rising difficulty — it will be "
            f"{'medium' if n_done <= 2 else 'hard'} this time."
        )
    else:
        rec_round = "multi_persona"
        reason = (
            f"You've completed {n_done} sessions for {target_company} already. "
            f"Time for a panel-style interview — three different interviewers "
            f"will take turns, just like a real placement panel."
        )

    auto_difficulty = (
        "easy" if n_done == 0 else ("medium" if n_done <= 2 else "hard")
    )

    return {
        "company":           target_company,
        "recommended_round": rec_round,
        "reason":            reason,
        "user_progress": {
            "completed_for_this_company":      n_done,
            "completed_across_all_companies":  sum(
                _company_completed_count(user_id, c) for c in VALID_COMPANIES
            ),
            "auto_difficulty_will_be":         auto_difficulty,
        },
        "all_round_options":  _ROUND_OPTIONS_FOR_FRONTEND,
        "all_companies":      VALID_COMPANIES,
        "valid_difficulties": list(VALID_DIFFICULTIES),
    }

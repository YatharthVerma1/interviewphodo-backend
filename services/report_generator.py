import logging
import time
import uuid
from collections import defaultdict

from services.interview_fsm import InterviewState
from services.speech_analyser import analyse_full_transcript, total_filler_count_for_state
from services.turn_scorer import build_turn_breakdown
from database.supabase_client import fetch_one, supabase_admin

logger = logging.getLogger(__name__)

# Any interview with at least one exchange should produce a report.
REPORT_GENERATION_REASONS = frozenset({
    "completed", "student_left", "manual_end", "time_capped", "error",
})


def _phase_scores_from_transcript(transcript: list) -> dict:
    buckets: dict[str, list] = defaultdict(list)
    for turn in transcript:
        score = turn.get("score")
        phase = turn.get("phase")
        if score is not None and phase:
            buckets[phase].append(score)
    return {
        phase: round(sum(scores) / len(scores), 1)
        for phase, scores in buckets.items()
        if scores
    }


def state_from_session_row(session: dict) -> InterviewState:
    """Rebuild in-memory interview state from a persisted session row."""
    state = InterviewState(
        session_id=session["id"],
        user_id=session["user_id"],
        company=session.get("company") or "tcs",
        round_type=session.get("round_type") or "coaching",
        resume_text=session.get("resume_text") or "",
    )
    state.transcript = session.get("transcript") or []
    state.filler_count = session.get("filler_count") or 0
    state.total_turns = session.get("total_turns") or len(state.transcript)
    state.posture_events = session.get("posture_events") or []
    state.phase_scores = _phase_scores_from_transcript(state.transcript)
    dur = session.get("duration_seconds")
    if dur and int(dur) > 0:
        state.started_at = time.time() - int(dur)
    return state


async def ensure_report_for_session(session_id: str, user_id: str) -> dict | None:
    """Return existing report or generate one from the session transcript in DB."""
    existing = fetch_one(
        supabase_admin.table("reports").select("*").eq("session_id", session_id)
    )
    if existing:
        return existing

    session = fetch_one(
        supabase_admin.table("sessions")
        .select(
            "id, user_id, company, round_type, transcript, filler_count, "
            "total_turns, posture_events, duration_seconds, status"
        )
        .eq("id", session_id)
    )
    if not session or session.get("user_id") != user_id:
        return None
    if not session.get("transcript"):
        return None

    state = state_from_session_row(session)
    await generate_report(state)
    return fetch_one(
        supabase_admin.table("reports").select("*").eq("session_id", session_id)
    )


async def generate_report(state: InterviewState):
    """Generate and save performance report after interview ends."""
    duration = state.get_interview_elapsed_seconds() or state.get_duration_seconds()
    speech   = analyse_full_transcript(state.transcript, duration)
    turn_breakdown = build_turn_breakdown(state.transcript)

    phase_scores = {
        phase: round(sum(scores) / len(scores), 1)
        for phase, scores in state.phase_scores.items()
        if scores
    }

    closing_summary = _extract_closing_summary(state.transcript)

    posture_score     = _posture_score(state.posture_events)
    eye_contact_score = _eye_contact_score(state.posture_events)

    report = {
        "session_id":         state.session_id,
        "user_id":            state.user_id,
        "overall_score":      state.get_overall_score(),
        "phase_scores":       phase_scores,
        "filler_count":       total_filler_count_for_state(state),
        "filler_percentage":  speech.get("filler_pct", 0.0),
        "words_per_minute":   speech.get("words_per_min", 0.0),
        "pace_verdict":       speech.get("pace_verdict", ""),
        "posture_score":      posture_score,
        "eye_contact_score":  eye_contact_score,
        "ai_closing_summary": closing_summary,
        "turn_breakdown":     turn_breakdown,
    }

    existing = fetch_one(
        supabase_admin.table("reports").select("id").eq("session_id", state.session_id)
    )
    try:
        if existing:
            supabase_admin.table("reports").update(report).eq(
                "session_id", state.session_id
            ).execute()
            logger.info(f"Report updated | session={state.session_id}")
        else:
            report["id"] = str(uuid.uuid4())
            supabase_admin.table("reports").insert(report).execute()
            logger.info(
                f"Report saved | session={state.session_id} "
                f"turns_scored={len(turn_breakdown)}"
            )
    except Exception as e:
        # turn_breakdown column may not exist yet — retry without it
        if "turn_breakdown" in str(e):
            report.pop("turn_breakdown", None)
            try:
                supabase_admin.table("reports").insert(report).execute()
                logger.warning(
                    f"Report saved without turn_breakdown (run migration 002). "
                    f"session={state.session_id}"
                )
            except Exception as e2:
                logger.error(f"Report save failed: {e2}")
        else:
            logger.error(f"Report save failed: {e}")


def _extract_closing_summary(transcript: list) -> str:
    """Pick the substantive closing report, not the short goodbye line."""
    closing_texts = [
        (t.get("ai_text") or "").strip()
        for t in transcript
        if t.get("phase") == "closing" and (t.get("ai_text") or "").strip()
    ]
    if not closing_texts:
        return ""

    # Longest closing turn is usually the structured performance report.
    substantial = [t for t in closing_texts if len(t) >= 120]
    if substantial:
        return max(substantial, key=len)

    # Skip one-line goodbyes if a longer closing turn exists.
    non_goodbye = [
        t for t in closing_texts
        if "goodbye" not in t.lower() or len(t) > 50
    ]
    if non_goodbye:
        return max(non_goodbye, key=len)

    return closing_texts[-1]


def _posture_score(events: list) -> int:
    if not events:
        return 85
    bad = sum(1 for e in events if e.get("type") == "slouching")
    return max(0, int(100 - (bad / len(events)) * 100))


def _eye_contact_score(events: list) -> int:
    if not events:
        return 80
    away = sum(1 for e in events if e.get("type") == "looking_away")
    return max(0, int(100 - (away / len(events)) * 100))


async def backfill_missing_reports(user_id: str, limit: int = 25) -> int:
    """Generate reports for past sessions that have transcripts but no report row."""
    rows = (
        supabase_admin.table("sessions")
        .select("id, transcript")
        .eq("user_id", user_id)
        .in_("status", ["completed", "abandoned"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )
    if not rows:
        return 0

    existing = (
        supabase_admin.table("reports")
        .select("session_id")
        .eq("user_id", user_id)
        .execute()
        .data or []
    )
    have = {r["session_id"] for r in existing}
    created = 0
    for row in rows:
        if row["id"] in have or not row.get("transcript"):
            continue
        try:
            rep = await ensure_report_for_session(row["id"], user_id)
            if rep:
                created += 1
        except Exception as e:
            logger.error(f"Backfill skipped session {row['id']}: {e}")
    return created

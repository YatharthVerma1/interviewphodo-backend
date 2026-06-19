import logging
from services.interview_fsm import InterviewState
from services.speech_analyser import analyse_full_transcript
from database.supabase_client import supabase_admin

logger = logging.getLogger(__name__)


async def generate_report(state: InterviewState):
    """Generate and save performance report after interview ends."""
    duration = state.get_duration_seconds()
    speech   = analyse_full_transcript(state.transcript, duration)

    phase_scores = {
        phase: round(sum(scores) / len(scores), 1)
        for phase, scores in state.phase_scores.items()
        if scores
    }

    # Get AI closing summary from last CLOSING phase turn
    closing_summary = next(
        (t["ai_text"] for t in reversed(state.transcript) if t.get("phase") == "closing"),
        ""
    )

    posture_score     = _posture_score(state.posture_events)
    eye_contact_score = _eye_contact_score(state.posture_events)

    report = {
        "session_id":         state.session_id,
        "user_id":            state.user_id,
        "overall_score":      state.get_overall_score(),
        "phase_scores":       phase_scores,
        "filler_count":       speech.get("filler_count", 0),
        "filler_percentage":  speech.get("filler_pct", 0.0),
        "words_per_minute":   speech.get("words_per_min", 0.0),
        "pace_verdict":       speech.get("pace_verdict", ""),
        "posture_score":      posture_score,
        "eye_contact_score":  eye_contact_score,
        "ai_closing_summary": closing_summary,
    }

    try:
        supabase_admin.table("reports").insert(report).execute()
        logger.info(f"Report saved | session={state.session_id}")
    except Exception as e:
        logger.error(f"Report save failed: {e}")


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

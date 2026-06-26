"""Recompute report metrics from session transcript when DB rows are stale."""

from __future__ import annotations

from services.speech_analyser import (
    analyse_full_transcript,
    count_fillers_in_transcript,
    detect_fillers_combined,
)
from services.interview_analysis import (
    analyse_session_star,
    delivery_score,
    turn_heatmap,
)
from services.turn_scorer import build_turn_breakdown, score_turn


def enrich_report_from_session(report: dict, session: dict | None) -> dict:
    """Fill missing filler/WPM/turn data from the session transcript."""
    if not session:
        return report

    transcript = session.get("transcript") or []
    duration = session.get("duration_seconds") or 0
    if duration <= 0:
        duration = 1

    speech = analyse_full_transcript(transcript, duration)
    enriched = dict(report)

    computed_fillers = count_fillers_in_transcript(transcript)
    session_fillers = session.get("filler_count") or 0
    best_filler = max(
        computed_fillers,
        session_fillers,
        enriched.get("filler_count") or 0,
    )
    enriched["filler_count"] = best_filler
    if speech.get("total_words", 0) > 0:
        enriched["filler_percentage"] = round(
            (best_filler / max(speech["total_words"], 1)) * 100, 1
        )
        if not enriched.get("words_per_minute"):
            enriched["words_per_minute"] = speech.get("words_per_min", 0.0)
            enriched["pace_verdict"] = speech.get("pace_verdict", "")

    breakdown = enriched.get("turn_breakdown") or build_turn_breakdown(transcript)
    if _needs_turn_rescore(breakdown, transcript):
        breakdown = _rescore_turns_from_transcript(transcript)
    enriched["turn_breakdown"] = breakdown

    if not enriched.get("overall_score") and breakdown:
        enriched["overall_score"] = round(
            sum(t["score"] for t in breakdown) / len(breakdown) * 10
        )

    star = analyse_session_star(transcript)
    if star:
        enriched["star_analysis"] = star

    delivery = delivery_score(
        enriched.get("posture_score"),
        enriched.get("eye_contact_score"),
        enriched.get("words_per_minute"),
        enriched.get("filler_percentage"),
    )
    enriched["delivery_score"] = delivery["overall"]
    enriched["delivery_breakdown"] = delivery

    enriched["question_heatmap"] = turn_heatmap(transcript, breakdown)

    return enriched


def _needs_turn_rescore(breakdown: list, transcript: list) -> bool:
    if not transcript:
        return False
    if not breakdown:
        return True
    no_answer = sum(
        1 for t in breakdown
        if "No answer detected" in (t.get("feedback") or "")
    )
    return no_answer >= max(1, len(breakdown) // 2)


def _rescore_turns_from_transcript(transcript: list) -> list:
    """Rebuild turn breakdown when stored feedback used empty student_text."""
    items = []
    for t in transcript:
        phase = t.get("phase", "")
        student = (t.get("student_text") or "").strip()
        if not student:
            continue
        fillers = t.get("filler_words") or detect_fillers_combined(
            student, t.get("ai_text") or ""
        )
        score, feedback = score_turn(
            phase=phase,
            student_text=student,
            ai_text=t.get("ai_text") or "",
            filler_words=fillers,
        )
        if score is None:
            continue
        items.append({
            "turn": t.get("turn"),
            "phase": phase,
            "score": score,
            "feedback": feedback,
            "student_preview": student[:120],
            "ai_preview": (t.get("ai_text") or "")[:80],
            "filler_count": len(fillers),
        })
    return items

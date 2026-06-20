"""
Progress aggregation — interviewphodo.com

Builds timeline + skill heatmap data from completed sessions and reports.
Used by GET /api/reports/my-progress for frontend charts.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from database.supabase_client import supabase_admin
from services.turn_scorer import build_turn_breakdown

# Map interview phases → skill buckets for the heatmap
_PHASE_TO_SKILL = {
    "technical_qa":  "technical",
    "resume_review": "communication",
    "behavioral":    "behavioral",
    "hr_round":      "hr_strategy",
    "intro":         "communication",
}


def build_user_progress(user_id: str, company: Optional[str] = None) -> dict:
    """Aggregate progress metrics across all completed sessions for a user."""
    query = (
        supabase_admin.table("sessions")
        .select(
            "id, company, round_type, status, "
            "transcript, duration_seconds, started_at, ended_at, created_at"
        )
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("created_at", desc=False)
    )
    if company:
        query = query.eq("company", company.lower())

    sessions = (query.execute().data or [])

    # Pull reports for richer metrics (filler, wpm, phase_scores, turn_breakdown)
    report_fields = (
        "session_id, overall_score, phase_scores, filler_count, "
        "filler_percentage, words_per_minute, pace_verdict, "
        "posture_score, eye_contact_score, created_at"
    )
    try:
        reports = (
            supabase_admin.table("reports")
            .select(report_fields + ", turn_breakdown")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
            .data or []
        )
    except Exception:
        reports = (
            supabase_admin.table("reports")
            .select(report_fields)
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
            .data or []
        )
    reports_by_session = {r["session_id"]: r for r in reports}

    if not sessions and not reports:
        return _empty_progress(company)

    # --- Timelines (for line charts) ---
    score_timeline: list[dict] = []
    filler_timeline: list[dict] = []
    wpm_timeline: list[dict] = []

    by_company: dict[str, dict] = defaultdict(lambda: {
        "sessions": 0, "scores": [], "latest_score": None,
    })
    phase_score_buckets: dict[str, list[float]] = defaultdict(list)
    skill_score_buckets: dict[str, list[float]] = defaultdict(list)

    for sess in sessions:
        sid = sess["id"]
        co = sess.get("company", "unknown")
        report = reports_by_session.get(sid, {})
        ts = report.get("created_at") or sess.get("created_at")

        overall = report.get("overall_score")
        if overall is None:
            # Derive from transcript turn scores if no report row yet
            breakdown = build_turn_breakdown(sess.get("transcript") or [])
            if breakdown:
                overall = round(sum(t["score"] for t in breakdown) / len(breakdown) * 10)

        if overall is not None:
            score_timeline.append({
                "session_id": sid,
                "company":    co,
                "round_type": sess.get("round_type"),
                "score":      overall,
                "date":       ts,
            })
            by_company[co]["scores"].append(overall)
            by_company[co]["latest_score"] = overall
        by_company[co]["sessions"] += 1

        filler = report.get("filler_count")
        if filler is not None:
            filler_timeline.append({
                "session_id": sid, "company": co, "value": filler, "date": ts,
            })

        wpm = report.get("words_per_minute")
        if wpm is not None:
            wpm_timeline.append({
                "session_id": sid, "company": co, "value": wpm, "date": ts,
            })

        # Phase + skill aggregation
        phase_scores = report.get("phase_scores") or {}
        for phase, avg in phase_scores.items():
            if isinstance(avg, (int, float)):
                phase_score_buckets[phase].append(float(avg))
                skill = _PHASE_TO_SKILL.get(phase)
                if skill:
                    skill_score_buckets[skill].append(float(avg))

        # Also mine per-turn scores from transcript / turn_breakdown
        breakdown = report.get("turn_breakdown") or build_turn_breakdown(
            sess.get("transcript") or []
        )
        for turn in breakdown:
            skill = _PHASE_TO_SKILL.get(turn.get("phase", ""))
            if skill and turn.get("score"):
                skill_score_buckets[skill].append(float(turn["score"]))

    # --- Company summary with trend ---
    company_summary = {}
    for co, data in by_company.items():
        scores = data["scores"]
        trend = None
        if len(scores) >= 2:
            trend = round(scores[-1] - scores[-2], 1)
        company_summary[co] = {
            "sessions":     data["sessions"],
            "avg_score":    round(sum(scores) / len(scores), 1) if scores else None,
            "latest_score": data["latest_score"],
            "trend":        trend,
        }

    by_phase_avg = {
        phase: round(sum(vals) / len(vals), 1)
        for phase, vals in phase_score_buckets.items()
        if vals
    }
    by_skill = {
        skill: round(sum(vals) / len(vals), 1)
        for skill, vals in skill_score_buckets.items()
        if vals
    }

    # Communication composite: average of communication bucket + inverse filler trend
    communication_score = by_skill.get("communication")
    if filler_timeline and len(filler_timeline) >= 2:
        filler_improving = filler_timeline[-1]["value"] < filler_timeline[0]["value"]
    else:
        filler_improving = None

    return {
        "filter_company":     company,
        "total_completed":    len(sessions),
        "total_with_reports": len(reports),
        "by_company":         company_summary,
        "score_timeline":     score_timeline,
        "filler_timeline":    filler_timeline,
        "wpm_timeline":       wpm_timeline,
        "by_phase_avg":       by_phase_avg,
        "by_skill":           by_skill,
        "insights": {
            "filler_improving":  filler_improving,
            "communication_score": communication_score,
            "strongest_skill":   max(by_skill, key=by_skill.get) if by_skill else None,
            "weakest_skill":     min(by_skill, key=by_skill.get) if by_skill else None,
        },
    }


def _empty_progress(company: Optional[str]) -> dict:
    return {
        "filter_company":     company,
        "total_completed":    0,
        "total_with_reports": 0,
        "by_company":         {},
        "score_timeline":     [],
        "filler_timeline":    [],
        "wpm_timeline":       [],
        "by_phase_avg":       {},
        "by_skill":           {},
        "insights": {
            "filler_improving":      None,
            "communication_score":   None,
            "strongest_skill":       None,
            "weakest_skill":         None,
        },
    }

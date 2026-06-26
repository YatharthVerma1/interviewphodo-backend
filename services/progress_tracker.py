"""
Progress aggregation — interviewphodo.com

Builds timeline + skill heatmap data from completed sessions and reports.
Used by GET /api/reports/my-progress for frontend charts.
"""

from __future__ import annotations

from collections import defaultdict

from services.interview_analysis import build_progress_insights
from typing import Optional

from database.supabase_client import supabase_admin
from services.report_enricher import enrich_report_from_session
from services.speech_analyser import analyse_full_transcript, count_fillers_in_transcript
from services.turn_scorer import build_turn_breakdown

# Map interview phases → skill buckets for the heatmap
_PHASE_TO_SKILL = {
    "technical_qa":  "technical",
    "resume_review": "communication",
    "behavioral":    "behavioral",
    "hr_round":      "hr_strategy",
    "intro":         "communication",
}


def _sort_timeline_by_date(items: list[dict]) -> list[dict]:
    """Oldest first, newest last — matches left-to-right chart axis."""
    return sorted(items, key=lambda x: x.get("date") or "")


def build_user_progress(user_id: str, company: Optional[str] = None) -> dict:
    """Aggregate progress metrics across all completed sessions for a user."""
    query = (
        supabase_admin.table("sessions")
        .select(
            "id, company, round_type, status, "
            "transcript, duration_seconds, filler_count, started_at, ended_at, created_at"
        )
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("created_at", desc=False)
    )
    if company:
        query = query.eq("company", company.lower())

    sessions = (query.execute().data or [])
    sessions_by_id = {s["id"]: s for s in sessions}

    # Also load non-completed sessions that have reports (e.g. manual end).
    if not company:
        extra_sessions = (
            supabase_admin.table("sessions")
            .select(
                "id, company, round_type, status, "
                "transcript, duration_seconds, filler_count, started_at, ended_at, created_at"
            )
            .eq("user_id", user_id)
            .in_("status", ["abandoned", "active", "pending"])
            .execute()
            .data or []
        )
        for sess in extra_sessions:
            sessions_by_id.setdefault(sess["id"], sess)

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
    processed_sids: set[str] = set()

    for sess in sessions:
        sid = sess["id"]
        co = sess.get("company", "unknown")
        report = enrich_report_from_session(
            reports_by_session.get(sid, {}),
            sessions_by_id.get(sid, sess),
        )
        ts = report.get("created_at") or sess.get("created_at")

        overall = report.get("overall_score")
        if overall is None:
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

        filler, wpm = _speech_metrics(report, sess)
        filler_timeline.append({
            "session_id": sid, "company": co, "value": filler, "date": ts,
        })
        wpm_timeline.append({
            "session_id": sid, "company": co, "value": wpm, "date": ts,
        })

        processed_sids.add(sid)

        # Phase + skill aggregation
        phase_scores = report.get("phase_scores") or {}
        for phase, avg in phase_scores.items():
            if isinstance(avg, (int, float)):
                phase_score_buckets[phase].append(float(avg))
                skill = _PHASE_TO_SKILL.get(phase)
                if skill:
                    skill_score_buckets[skill].append(float(avg))

        breakdown = report.get("turn_breakdown") or build_turn_breakdown(
            sess.get("transcript") or []
        )
        for turn in breakdown:
            skill = _PHASE_TO_SKILL.get(turn.get("phase", ""))
            if skill and turn.get("score"):
                skill_score_buckets[skill].append(float(turn["score"]))

    # Reports for sessions not in the completed-only query (e.g. abandoned).
    for report in reports:
        sid = report["session_id"]
        if sid in processed_sids:
            continue
        sess = sessions_by_id.get(sid)
        if not sess:
            continue
        enriched = enrich_report_from_session(report, sess)
        ts = enriched.get("created_at") or sess.get("created_at")
        co = sess.get("company", "unknown")
        overall = enriched.get("overall_score")
        if overall is not None:
            score_timeline.append({
                "session_id": sid,
                "company": co,
                "round_type": sess.get("round_type"),
                "score": overall,
                "date": ts,
            })
            by_company[co]["scores"].append(overall)
            by_company[co]["latest_score"] = overall
        by_company[co]["sessions"] += 1
        filler, wpm = _speech_metrics(enriched, sess)
        filler_timeline.append({
            "session_id": sid, "company": co, "value": filler, "date": ts,
        })
        wpm_timeline.append({
            "session_id": sid, "company": co, "value": wpm, "date": ts,
        })
        processed_sids.add(sid)

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

    result = {
        "filter_company":     company,
        "total_completed":    len(sessions),
        "total_with_reports": len(reports),
        "by_company":         company_summary,
        "score_timeline":     _sort_timeline_by_date(score_timeline),
        "filler_timeline":    _sort_timeline_by_date(filler_timeline),
        "wpm_timeline":       _sort_timeline_by_date(wpm_timeline),
        "by_phase_avg":       by_phase_avg,
        "by_skill":           by_skill,
        "insights": {
            "filler_improving":  filler_improving,
            "communication_score": communication_score,
            "strongest_skill":   max(by_skill, key=by_skill.get) if by_skill else None,
            "weakest_skill":     min(by_skill, key=by_skill.get) if by_skill else None,
        },
    }
    result["performance_insights"] = build_progress_insights(result)
    return result


def _speech_metrics(report: dict, session: dict) -> tuple[int, float]:
    speech = analyse_full_transcript(
        session.get("transcript") or [],
        session.get("duration_seconds") or 1,
    )
    filler = max(
        count_fillers_in_transcript(session.get("transcript") or []),
        session.get("filler_count") or 0,
        report.get("filler_count") or 0,
        speech.get("filler_count", 0),
    )
    wpm = speech.get("words_per_min", 0) or report.get("words_per_minute") or 0
    return int(filler), float(wpm)


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
        "performance_insights": {"going_well": [], "work_on": []},
    }

"""Adapt backend progress payload to Replit frontend ProgressData shape."""

from __future__ import annotations

from collections import defaultdict


def adapt_progress_for_frontend(data: dict) -> dict:
    """Merge detailed progress with fields expected by progress.tsx."""
    score_timeline = data.get("score_timeline") or []
    scores = [s["score"] for s in score_timeline if s.get("score") is not None]

    sessions_by_company = {
        k: v.get("sessions", 0)
        for k, v in (data.get("by_company") or {}).items()
    }

    sessions_by_round = data.get("sessions_by_round") or {}

    return {
        **data,
        "total_sessions": data.get("total_completed") or data.get("total_with_reports") or 0,
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "best_score": max(scores) if scores else 0,
        "sessions_by_company": sessions_by_company,
        "sessions_by_round": sessions_by_round,
        "score_trend": [
            {"date": item.get("date"), "score": item.get("score")}
            for item in score_timeline
            if item.get("date") is not None and item.get("score") is not None
        ],
    }


def build_sessions_by_round(user_id: str) -> dict[str, int]:
    from database.supabase_client import supabase_admin

    rows = (
        supabase_admin.table("sessions")
        .select("round_type")
        .eq("user_id", user_id)
        .in_("status", ["completed", "abandoned"])
        .execute()
        .data or []
    )
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        rt = row.get("round_type") or "unknown"
        counts[rt] += 1
    return dict(counts)

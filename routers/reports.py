from typing import Optional

from loguru import logger

from fastapi import APIRouter, Depends, HTTPException, Query
from routers.auth import get_current_user
from models.report import ReportResponse
from database.supabase_client import fetch_one, supabase_admin
from services.progress_tracker import build_user_progress
from services.progress_adapter import adapt_progress_for_frontend, build_sessions_by_round
from services.report_enricher import enrich_report_from_session
from services.report_generator import backfill_missing_reports, ensure_report_for_session
from services.turn_scorer import build_turn_breakdown

router = APIRouter()


async def _safe_backfill(user_id: str, limit: int = 25) -> None:
    """Backfill reports without failing the HTTP request if one session errors."""
    try:
        await backfill_missing_reports(user_id, limit=limit)
    except Exception as e:
        logger.error(f"Report backfill failed for user {user_id}: {e}")


def _enrich_report_with_turns(report: dict, session_id: str) -> dict:
    """Enrich report with turn breakdown and recomputed speech metrics."""
    session = fetch_one(
        supabase_admin.table("sessions")
        .select("transcript, duration_seconds, status, company, round_type")
        .eq("id", session_id)
    )
    report = enrich_report_from_session(report, session)
    if not report.get("turn_breakdown") and session and session.get("transcript"):
        report["turn_breakdown"] = build_turn_breakdown(session["transcript"])
    elif not report.get("turn_breakdown"):
        report["turn_breakdown"] = []
    return report


@router.get("/session/{session_id}", response_model=ReportResponse)
async def get_report(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = fetch_one(
        supabase_admin.table("sessions").select("user_id").eq("id", session_id)
    )
    if not session:
        raise HTTPException(404, "Session not found")
    if session["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized")

    report = fetch_one(
        supabase_admin.table("reports").select("*").eq("session_id", session_id)
    )
    if not report:
        report = await ensure_report_for_session(session_id, current_user["id"])
    if not report:
        raise HTTPException(404, "Report not ready yet — session may still be completing")

    return _enrich_report_with_turns(report, session_id)


@router.get("/session/{session_id}/turns")
async def get_session_turns(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Per-turn feedback for one session — usable even before report row exists."""
    session = fetch_one(
        supabase_admin.table("sessions")
        .select("user_id, status, transcript, company, round_type")
        .eq("id", session_id)
    )
    if not session:
        raise HTTPException(404, "Session not found")
    if session["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized")

    breakdown = build_turn_breakdown(session.get("transcript") or [])
    return breakdown


@router.get("/my-progress")
async def my_progress(
    company: Optional[str] = Query(
        None,
        description="Filter progress to one company (e.g. tcs). Omit for all companies.",
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Progress data for charts — score timeline, filler trend, WPM trend,
    per-phase averages, and skill heatmap buckets.
    """
    if company and company.lower() not in {
        "tcs", "infosys", "wipro", "hcl", "accenture",
        "cognizant", "tech_mahindra", "zoho",
    }:
        raise HTTPException(400, "Invalid company filter")

    await _safe_backfill(current_user["id"])
    data = build_user_progress(current_user["id"], company=company)
    data["sessions_by_round"] = build_sessions_by_round(current_user["id"])
    return adapt_progress_for_frontend(data)


@router.get("/my-reports")
async def my_reports(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
):
    await _safe_backfill(current_user["id"], limit=limit + 15)
    rows = supabase_admin.table("reports").select(
        "id, session_id, overall_score, phase_scores, filler_count, "
        "words_per_minute, pace_verdict, posture_score, created_at, turn_breakdown"
    ).eq("user_id", current_user["id"]).order(
        "created_at", desc=True
    ).limit(limit).execute()

    session_ids = [r["session_id"] for r in (rows.data or [])]
    sessions_by_id = {}
    if session_ids:
        sess_rows =         supabase_admin.table("sessions").select(
            "id, transcript, duration_seconds, filler_count, status, company, round_type"
        ).in_("id", session_ids).execute()
        sessions_by_id = {s["id"]: s for s in (sess_rows.data or [])}

    enriched = []
    for r in (rows.data or []):
        sess = sessions_by_id.get(r["session_id"])
        item = enrich_report_from_session(r, sess)
        if sess:
            item["company"] = sess.get("company")
            item["round_type"] = sess.get("round_type")
        enriched.append(item)
    return enriched

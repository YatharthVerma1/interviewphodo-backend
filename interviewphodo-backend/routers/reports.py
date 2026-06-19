from fastapi import APIRouter, Depends, HTTPException
from routers.auth import get_current_user
from models.report import ReportResponse
from database.supabase_client import supabase_admin

router = APIRouter()


@router.get("/session/{session_id}", response_model=ReportResponse)
async def get_report(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = supabase_admin.table("sessions").select("user_id").eq(
        "id", session_id
    ).single().execute()

    if not session.data or session.data["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized")

    report = supabase_admin.table("reports").select("*").eq(
        "session_id", session_id
    ).single().execute()

    if not report.data:
        raise HTTPException(404, "Report not ready yet — session may still be completing")

    return report.data


@router.get("/my-reports")
async def my_reports(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
):
    rows = supabase_admin.table("reports").select(
        "id, session_id, overall_score, phase_scores, filler_count, "
        "words_per_minute, pace_verdict, posture_score, created_at"
    ).eq("user_id", current_user["id"]).order(
        "created_at", desc=True
    ).limit(limit).execute()
    return rows.data

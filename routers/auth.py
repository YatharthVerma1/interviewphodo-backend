import uuid
import io
import os
from pathlib import Path

import boto3
from botocore.client import Config
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database.supabase_client import supabase_admin
from models.user import UserProfile, UserUpdateRequest
from prompts.role_pools import normalize_target_role, normalize_timeline
from config import settings
from services.credits import owner_profile_view

LOCAL_UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads" / "resumes"

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validates Supabase JWT sent as: Authorization: Bearer <token>
    Returns the user's row from public.users table.
    This function is used as a FastAPI Dependency in all protected routes.
    """
    if not settings.supabase_configured:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env",
        )

    token = credentials.credentials.strip()

    try:
        auth_response = supabase_admin.auth.get_user(token)
        user_id = auth_response.user.id

        profile = supabase_admin.table("users") \
            .select("*") \
            .eq("id", user_id) \
            .single() \
            .execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        return profile.data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    return owner_profile_view(current_user)


@router.patch("/me")
async def update_profile(
    updates: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    payload = updates.model_dump(exclude_none=True)
    if "target_role" in payload:
        payload["target_role"] = normalize_target_role(payload["target_role"])
    if "interview_timeline" in payload:
        payload["interview_timeline"] = normalize_timeline(payload["interview_timeline"])
    if not payload:
        return current_user
    try:
        result = supabase_admin.table("users") \
            .update(payload) \
            .eq("id", current_user["id"]) \
            .execute()
        return result.data[0]
    except Exception:
        # Graceful fallback if migration 003 not applied yet
        payload.pop("target_role", None)
        payload.pop("interview_timeline", None)
        if not payload:
            return current_user
        result = supabase_admin.table("users") \
            .update(payload) \
            .eq("id", current_user["id"]) \
            .execute()
        return result.data[0]


@router.post("/upload-resume")
async def upload_resume(
    request: Request,
    current_user: dict = Depends(get_current_user),
    file: UploadFile | None = File(None),
    resume: UploadFile | None = File(None),
):
    """
    Student uploads resume PDF.

    Accepts form field ``file`` (OpenAPI default) or ``resume`` (Replit frontend).
    """
    upload = file or resume
    if upload is None:
        raise HTTPException(400, "Missing file — use form field 'file' or 'resume'")

    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    content = await upload.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large — max 5MB")

    file_key = f"{current_user['id']}/{uuid.uuid4().hex}.pdf"

    if settings.r2_configured:
        r2 = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        try:
            r2.put_object(
                Bucket=settings.r2_bucket_name,
                Key=f"resumes/{file_key}",
                Body=content,
                ContentType="application/pdf",
            )
            resume_url = f"{settings.r2_endpoint}/{settings.r2_bucket_name}/resumes/{file_key}"
            storage = "r2"
        except Exception as e:
            raise HTTPException(500, f"R2 upload failed: {str(e)}")
    else:
        local_path = LOCAL_UPLOAD_ROOT / file_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            local_path.write_bytes(content)
        except OSError as e:
            raise HTTPException(500, f"Local save failed: {e}")
        base = str(request.base_url).rstrip("/")
        resume_url = f"{base}/uploads/resumes/{file_key}"
        storage = "local"

    resume_text = _extract_pdf_text(content)

    supabase_admin.table("users").update({
        "resume_url": resume_url,
        "resume_text": resume_text[:3000],
    }).eq("id", current_user["id"]).execute()

    return {
        "status": "uploaded",
        "storage": storage,
        "resume_url": resume_url,
        "text_length": len(resume_text),
        "preview": resume_text[:150] + "..." if len(resume_text) > 150 else resume_text,
    }


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        return "Resume text extraction failed. Interviewer will ask about projects directly."

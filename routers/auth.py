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
from config import settings

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
    return current_user


@router.patch("/me")
async def update_profile(
    updates: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    result = supabase_admin.table("users") \
        .update(updates.model_dump(exclude_none=True)) \
        .eq("id", current_user["id"]) \
        .execute()
    return result.data[0]


@router.post("/upload-resume")
async def upload_resume(
     request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Student uploads resume PDF.

    - If Cloudflare R2 is configured -> uploads to R2.
    - Otherwise -> saves to local ``uploads/resumes/`` folder (dev fallback).

    In both cases the PDF text is extracted and saved on the user row so the
    interviewer prompt can reference the candidate's projects.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    content = await file.read()

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

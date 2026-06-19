import uuid
import io
import boto3
from botocore.client import Config
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from database.supabase_client import supabase_admin
from models.user import UserProfile, UserUpdateRequest
from config import settings

router = APIRouter()


async def get_current_user(authorization: str = Header(...)) -> dict:
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

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "").strip()

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
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Student uploads resume PDF.
    Saves file to Cloudflare R2.
    Extracts text for injection into FSM interview prompts.
    Saves resume_url and resume_text to users table.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large — max 5MB")

    if not settings.r2_configured:
        raise HTTPException(
            status_code=503,
            detail="Resume upload is not configured yet. Set R2_* environment variables.",
        )

    # Upload to Cloudflare R2
    file_key = f"resumes/{current_user['id']}/{uuid.uuid4().hex}.pdf"
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
            Key=file_key,
            Body=content,
            ContentType="application/pdf",
        )
        resume_url = f"{settings.r2_endpoint}/{settings.r2_bucket_name}/{file_key}"
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

    # Extract text from PDF for prompt injection
    resume_text = _extract_pdf_text(content)

    supabase_admin.table("users").update({
        "resume_url": resume_url,
        "resume_text": resume_text[:3000],
    }).eq("id", current_user["id"]).execute()

    return {
        "status": "uploaded",
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

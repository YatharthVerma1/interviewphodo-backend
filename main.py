from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import auth, avatar_ws, payments, reports, sessions

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="interviewphodo.com API",
    description="Real-time AI mock interviewer for Indian BTech students",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(avatar_ws.router, prefix="/ws", tags=["avatar"])

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "interviewphodo.com API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "product": "interviewphodo.com",
        "services": {
            "supabase": settings.supabase_configured,
            "daily": settings.daily_configured,
            "google": settings.google_configured,
            "r2": settings.r2_configured,
            "razorpay": settings.razorpay_configured,
        },
    }

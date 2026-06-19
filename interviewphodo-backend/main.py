from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import auth, avatar_ws, payments, reports, sessions

app = FastAPI(
    title="interviewphodo.com API",
    description="Real-time AI mock interviewer for Indian BTech students",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(avatar_ws.router, prefix="/ws", tags=["avatar"])


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

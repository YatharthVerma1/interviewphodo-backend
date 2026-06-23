import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from config import settings
from database.supabase_client import fetch_one, supabase_admin
from routers.auth import get_current_user
from services.credits import enrich_profile_subscription, owner_profile_view
from services.pricing import PAYMENT_PACKS, plans_for_api
from services.subscription import activate_paid_subscription

router = APIRouter()

PACKS = PAYMENT_PACKS


class OrderRequest(BaseModel):
    pack_type: str


def _get_razorpay_client():
    if not settings.razorpay_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Payments are not enabled in this environment. "
                "Razorpay integration is deferred — for now, activate plans "
                "manually in Supabase (plan, sessions_limit, subscription_ends_at)."
            ),
        )
    import razorpay
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


@router.get("/plans")
async def list_plans():
    """Public pricing plans with credit costs and access windows."""
    return {"plans": plans_for_api()}


@router.get("/subscription")
async def my_subscription(current_user: dict = Depends(get_current_user)):
    """Current user's plan, credits, and access window (synced / expiry-checked)."""
    view = owner_profile_view(enrich_profile_subscription(current_user))
    return {
        "plan": view.get("plan"),
        "plan_label": view.get("plan_label"),
        "credits_used": view.get("sessions_used", 0),
        "credits_limit": view.get("sessions_limit", 0),
        "credits_remaining": view.get("credits_remaining", 0),
        "subscription_starts_at": view.get("subscription_starts_at"),
        "subscription_ends_at": view.get("subscription_ends_at"),
        "subscription_active": view.get("subscription_active"),
        "subscription_days_left": view.get("subscription_days_left"),
        "can_start_interview": view.get("can_start_interview"),
        "access_blocked_reason": view.get("access_blocked_reason"),
        "access_message": view.get("access_message"),
    }


@router.post("/create-order")
async def create_order(
    body: OrderRequest,
    current_user: dict = Depends(get_current_user),
):
    pack = PACKS.get(body.pack_type)
    if not pack:
        raise HTTPException(400, f"Invalid pack. Choose: {list(PACKS.keys())}")

    rp = _get_razorpay_client()

    try:
        order = rp.order.create({
            "amount": pack["amount_paise"],
            "currency": "INR",
            "notes": {
                "user_id": current_user["id"],
                "pack": body.pack_type,
                "product": "interviewphodo.com",
            },
        })
    except Exception as e:
        raise HTTPException(500, f"Razorpay order creation failed: {str(e)}")

    supabase_admin.table("payment_orders").insert({
        "user_id": current_user["id"],
        "razorpay_order_id": order["id"],
        "amount_paise": pack["amount_paise"],
        "pack_type": body.pack_type,
        "sessions_granted": pack["credits"],
    }).execute()

    return {
        "order_id": order["id"],
        "amount": pack["amount_paise"],
        "currency": "INR",
        "razorpay_key": settings.razorpay_key_id,
        "pack_label": pack["label"],
        "credits": pack["credits"],
        "access_days": pack["access_days"],
        "plan": pack["plan"],
    }


@router.post("/verify-payment")
async def verify_payment(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if not settings.razorpay_configured:
        raise HTTPException(status_code=503, detail="Payments are not configured yet.")

    body = await request.json()
    order_id = body.get("razorpay_order_id")
    payment_id = body.get("razorpay_payment_id")
    signature = body.get("razorpay_signature")

    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected != signature:
        raise HTTPException(400, "Invalid payment signature")

    order_row = fetch_one(
        supabase_admin.table("payment_orders")
        .select("*")
        .eq("razorpay_order_id", order_id)
    )
    if not order_row:
        raise HTTPException(404, "Order not found")

    if order_row["status"] == "paid":
        return {"status": "already_processed"}

    pack = PACKS.get(order_row["pack_type"], {})
    plan_name = pack.get("plan", order_row["pack_type"])
    credits_granted = int(pack.get("credits") or order_row["sessions_granted"])

    try:
        updated_user = activate_paid_subscription(current_user["id"], plan_name)
    except Exception as e:
        raise HTTPException(500, f"Failed to activate subscription: {e}")

    supabase_admin.table("payment_orders").update({
        "status": "paid",
        "razorpay_payment_id": payment_id,
        "paid_at": "now()",
    }).eq("razorpay_order_id", order_id).execute()

    view = enrich_profile_subscription(updated_user)
    return {
        "status": "success",
        "plan": plan_name,
        "credits_granted": credits_granted,
        "credits_remaining": view.get("credits_remaining"),
        "subscription_starts_at": view.get("subscription_starts_at"),
        "subscription_ends_at": view.get("subscription_ends_at"),
        "subscription_days_left": view.get("subscription_days_left"),
    }


@router.get("/my-orders")
async def my_orders(current_user: dict = Depends(get_current_user)):
    rows = supabase_admin.table("payment_orders").select(
        "id, pack_type, amount_paise, sessions_granted, status, created_at, paid_at"
    ).eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
    return rows.data

import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from config import settings
from database.supabase_client import supabase_admin
from routers.auth import get_current_user

router = APIRouter()

PACKS = {
    "trial": {"amount_paise": 9900, "sessions": 2, "label": "Trial — 2 sessions"},
    "starter": {"amount_paise": 24900, "sessions": 5, "label": "Starter — 5 sessions"},
    "standard": {"amount_paise": 44900, "sessions": 10, "label": "Standard — 10 sessions"},
}


class OrderRequest(BaseModel):
    pack_type: str


def _get_razorpay_client():
    if not settings.razorpay_configured:
        raise HTTPException(
            status_code=503,
            detail="Payments are not configured yet. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env",
        )
    import razorpay
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


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
        "sessions_granted": pack["sessions"],
    }).execute()

    return {
        "order_id": order["id"],
        "amount": pack["amount_paise"],
        "currency": "INR",
        "razorpay_key": settings.razorpay_key_id,
        "pack_label": pack["label"],
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

    order_row = supabase_admin.table("payment_orders").select("*").eq(
        "razorpay_order_id", order_id
    ).single().execute()

    if not order_row.data:
        raise HTTPException(404, "Order not found")

    if order_row.data["status"] == "paid":
        return {"status": "already_processed"}

    sessions_to_add = order_row.data["sessions_granted"]

    user = supabase_admin.table("users").select(
        "sessions_limit"
    ).eq("id", current_user["id"]).single().execute()

    new_limit = user.data["sessions_limit"] + sessions_to_add

    supabase_admin.table("users").update({
        "sessions_limit": new_limit
    }).eq("id", current_user["id"]).execute()

    supabase_admin.table("payment_orders").update({
        "status": "paid",
        "razorpay_payment_id": payment_id,
        "paid_at": "now()",
    }).eq("razorpay_order_id", order_id).execute()

    return {
        "status": "success",
        "sessions_added": sessions_to_add,
        "new_session_limit": new_limit,
    }


@router.get("/my-orders")
async def my_orders(current_user: dict = Depends(get_current_user)):
    rows = supabase_admin.table("payment_orders").select(
        "id, pack_type, amount_paise, sessions_granted, status, created_at, paid_at"
    ).eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
    return rows.data

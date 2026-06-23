"""Subscription + credit access control.

Rules
-----
Free:
  - 3 credits on signup, no time limit — for testing the product.
Paid (Starter / Pro):
  - Fixed access window (30 / 60 days) AND a fixed credit pool (11 / 40).
  - User must have BOTH an active window AND enough credits to start an interview.
  - If the window ends → downgrade to free with 0 credits left (reports/dashboard kept).
  - If credits run out before the window ends → cannot interview until repurchase.
  - Repurchase resets credits and starts a fresh access window (does not stack).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from database.supabase_client import supabase_admin
from services.pricing import (
    PAID_PLAN_IDS,
    PRO_ONLY_ROUNDS,
    VIDEO_INTERVIEW_CREDITS,
    VOICE_INTERVIEW_CREDITS,
    plan_config,
)

logger = logging.getLogger(__name__)

InterviewMode = Literal["voice", "video"]

USER_SUBSCRIPTION_FIELDS = (
    "id, email, plan, sessions_used, sessions_limit, "
    "subscription_starts_at, subscription_ends_at"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_paid_plan(plan: str | None) -> bool:
    return (plan or "free").lower() in PAID_PLAN_IDS


def credit_cost(mode: InterviewMode = "video") -> int:
    return VOICE_INTERVIEW_CREDITS if mode == "voice" else VIDEO_INTERVIEW_CREDITS


def credits_remaining(user_row: dict[str, Any]) -> int:
    used = int(user_row.get("sessions_used") or 0)
    limit = int(user_row.get("sessions_limit") or 0)
    return max(0, limit - used)


def subscription_ends_at(user_row: dict[str, Any]) -> datetime | None:
    return parse_utc(user_row.get("subscription_ends_at"))


def subscription_is_active(user_row: dict[str, Any], *, at: datetime | None = None) -> bool:
    plan = (user_row.get("plan") or "free").lower()
    if not is_paid_plan(plan):
        return True
    ends = subscription_ends_at(user_row)
    if ends is None:
        return False
    now = at or utc_now()
    return now < ends


def subscription_expired(user_row: dict[str, Any], *, at: datetime | None = None) -> bool:
    plan = (user_row.get("plan") or "free").lower()
    if not is_paid_plan(plan):
        return False
    ends = subscription_ends_at(user_row)
    if ends is None:
        return True
    now = at or utc_now()
    return now >= ends


def days_until_expiry(user_row: dict[str, Any], *, at: datetime | None = None) -> int | None:
    if not is_paid_plan(user_row.get("plan")):
        return None
    ends = subscription_ends_at(user_row)
    if ends is None:
        return None
    now = at or utc_now()
    if now >= ends:
        return 0
    return max(0, (ends - now).days)


def downgrade_expired_payload(user_row: dict[str, Any]) -> dict[str, Any]:
    """Build DB update when a paid plan's access window has ended."""
    used = int(user_row.get("sessions_used") or 0)
    return {
        "plan": "free",
        "sessions_limit": used,
        "subscription_starts_at": None,
        "subscription_ends_at": None,
    }


def sync_subscription_state(user_row: dict[str, Any]) -> dict[str, Any]:
    """If paid access expired, downgrade in DB and return the fresh row."""
    if not subscription_expired(user_row):
        return user_row

    user_id = user_row.get("id")
    if not user_id:
        return user_row

    payload = downgrade_expired_payload(user_row)
    try:
        result = (
            supabase_admin.table("users")
            .update(payload)
            .eq("id", user_id)
            .execute()
        )
        if result.data:
            logger.info(
                f"Subscription expired — downgraded to free | user={user_id} "
                f"prev_plan={user_row.get('plan')}"
            )
            return result.data[0]
    except Exception as e:
        logger.error(f"Failed to downgrade expired subscription | user={user_id}: {e}")

    merged = dict(user_row)
    merged.update(payload)
    return merged


def fetch_user_subscription_row(user_id: str) -> dict[str, Any] | None:
    try:
        result = (
            supabase_admin.table("users")
            .select(USER_SUBSCRIPTION_FIELDS)
            .eq("id", user_id)
            .single()
            .execute()
        )
        return result.data
    except Exception:
        return None


def get_user_with_synced_subscription(
    user_row: dict[str, Any],
    *,
    jwt_email: str | None = None,
) -> dict[str, Any]:
    from services.credits import is_owner_user

    if is_owner_user(user_row, jwt_email=jwt_email):
        return user_row
    return sync_subscription_state(user_row)


def activate_paid_subscription(user_id: str, plan_id: str) -> dict[str, Any]:
    """Apply a fresh paid subscription after successful payment."""
    plan_key = plan_id.lower()
    if plan_key not in PAID_PLAN_IDS:
        raise ValueError(f"Not a paid plan: {plan_id}")

    cfg = plan_config(plan_key)
    access_days = int(cfg["access_days"])
    credits = int(cfg["credits"])
    now = utc_now()
    ends = now + timedelta(days=access_days)

    payload = {
        "plan": plan_key,
        "sessions_used": 0,
        "sessions_limit": credits,
        "subscription_starts_at": now.isoformat(),
        "subscription_ends_at": ends.isoformat(),
    }

    result = (
        supabase_admin.table("users")
        .update(payload)
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise RuntimeError(f"Failed to activate subscription for user {user_id}")

    logger.info(
        f"Activated {plan_key} | user={user_id} credits={credits} "
        f"ends={ends.isoformat()}"
    )
    return result.data[0]


def round_requires_pro(round_type: str) -> bool:
    return round_type.lower() in PRO_ONLY_ROUNDS


def plan_allows_round(user_row: dict[str, Any], round_type: str) -> bool:
    from services.credits import is_owner_user

    if is_owner_user(user_row):
        return True
    if not round_requires_pro(round_type):
        return True
    plan = (user_row.get("plan") or "free").lower()
    return plan == "pro"


def interview_access_status(
    user_row: dict[str, Any],
    *,
    mode: InterviewMode = "video",
    round_type: str | None = None,
    is_owner: bool = False,
) -> dict[str, Any]:
    """Explain whether the user can start an interview right now."""
    if is_owner:
        return {
            "can_start": True,
            "reason": None,
            "message": None,
            "credits_remaining": 999999,
            "subscription_active": True,
            "plan": "pro",
        }

    user_row = sync_subscription_state(user_row)
    plan = (user_row.get("plan") or "free").lower()
    remaining = credits_remaining(user_row)
    cost = credit_cost(mode)
    active = subscription_is_active(user_row)

    if round_type and not plan_allows_round(user_row, round_type):
        return {
            "can_start": False,
            "reason": "pro_required",
            "message": "Panel (multi-persona) round requires the Pro plan.",
            "credits_remaining": remaining,
            "subscription_active": active,
            "plan": plan,
        }

    if is_paid_plan(plan) and not active:
        return {
            "can_start": False,
            "reason": "subscription_expired",
            "message": (
                "Your paid plan access period has ended. "
                "Repurchase a plan for fresh credits. Your reports and dashboard are still available."
            ),
            "credits_remaining": remaining,
            "subscription_active": False,
            "plan": plan,
        }

    if remaining < cost:
        if is_paid_plan(plan):
            msg = (
                "You have used all credits on your current plan. "
                "Repurchase to get a fresh credit pool and access window."
            )
            reason = "credits_exhausted_paid"
        else:
            msg = (
                f"Not enough credits for a {mode} interview ({cost} required). "
                "Upgrade at interviewphodo.com/#pricing"
            )
            reason = "credits_exhausted_free"
        return {
            "can_start": False,
            "reason": reason,
            "message": msg,
            "credits_remaining": remaining,
            "subscription_active": active,
            "plan": plan,
        }

    return {
        "can_start": True,
        "reason": None,
        "message": None,
        "credits_remaining": remaining,
        "subscription_active": active,
        "plan": plan,
    }


def can_start_interview(
    user_row: dict[str, Any],
    email: str | None,
    *,
    mode: InterviewMode = "video",
    round_type: str | None = None,
    is_owner: bool = False,
) -> bool:
    from services.credits import is_owner_user

    owner = is_owner or is_owner_user({"email": email})
    status = interview_access_status(
        user_row, mode=mode, round_type=round_type, is_owner=owner
    )
    return bool(status["can_start"])


def enrich_profile_subscription(user_row: dict[str, Any]) -> dict[str, Any]:
    """Add computed subscription fields for API responses."""
    user_row = sync_subscription_state(user_row)
    plan = (user_row.get("plan") or "free").lower()
    remaining = credits_remaining(user_row)
    active = subscription_is_active(user_row)
    access = interview_access_status(user_row)

    out = dict(user_row)
    out["credits_remaining"] = remaining
    out["subscription_active"] = active
    out["subscription_days_left"] = days_until_expiry(user_row)
    out["can_start_interview"] = access["can_start"]
    out["access_blocked_reason"] = access.get("reason")
    out["access_message"] = access.get("message")
    out["plan_label"] = plan_config(plan).get("name", plan.title())
    out["is_paid_plan"] = is_paid_plan(plan)
    return out

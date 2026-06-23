"""Credit checks — delegates to subscription.py. Owner bypass via OWNER_EMAILS."""

from __future__ import annotations

from typing import Any, Literal

from config import settings
from services.subscription import (
    InterviewMode,
    can_start_interview,
    credit_cost,
    credits_remaining,
    enrich_profile_subscription,
    get_user_with_synced_subscription,
    interview_access_status,
)

__all__ = [
    "InterviewMode",
    "credit_cost",
    "credits_remaining",
    "is_owner_user",
    "owner_profile_view",
    "has_sessions_remaining",
    "has_credits_remaining",
    "get_user_with_synced_subscription",
    "enrich_profile_subscription",
    "interview_access_status",
    "OWNER_UNLIMITED_CREDITS",
]

# Effectively infinite for owner testing accounts.
OWNER_UNLIMITED_CREDITS = 999_999


def is_owner_user(user: dict[str, Any] | str | None, *, jwt_email: str | None = None) -> bool:
    if user is None and not jwt_email:
        return False
    if isinstance(user, str):
        emails = [user]
    else:
        emails = [user.get("email")]
    if jwt_email:
        emails.append(jwt_email)
    return any(settings.is_owner_email(e) for e in emails if e)


def owner_profile_view(profile: dict[str, Any], *, jwt_email: str | None = None) -> dict[str, Any]:
    """Owners see lifetime Pro with unlimited credits — never expires or deducts."""
    if not is_owner_user(profile, jwt_email=jwt_email):
        return enrich_profile_subscription(profile)
    out = dict(profile)
    used = int(out.get("sessions_used") or 0)
    out["is_owner"] = True
    out["owner_lifetime_access"] = True
    out["plan"] = "pro"
    out["plan_label"] = "Pro"
    out["is_paid_plan"] = True
    out["sessions_limit"] = used + OWNER_UNLIMITED_CREDITS
    out["credits_remaining"] = OWNER_UNLIMITED_CREDITS
    out["subscription_active"] = True
    out["subscription_days_left"] = None
    out["can_start_interview"] = True
    out["access_blocked_reason"] = None
    out["access_message"] = None
    return out


def has_sessions_remaining(
    user_row: dict[str, Any],
    email: str | None,
    *,
    mode: InterviewMode = "video",
    round_type: str | None = None,
) -> bool:
    if is_owner_user({"email": email}):
        return True
    user_row = get_user_with_synced_subscription(user_row)
    return can_start_interview(
        user_row,
        email,
        mode=mode,
        round_type=round_type,
        is_owner=False,
    )


has_credits_remaining = has_sessions_remaining

"""Session credit checks — owner bypass via OWNER_EMAILS in .env (never committed)."""

from __future__ import annotations

from typing import Any

from config import settings


def is_owner_user(user: dict[str, Any] | str | None) -> bool:
    if user is None:
        return False
    email = user if isinstance(user, str) else user.get("email")
    return settings.is_owner_email(email)


def owner_profile_view(profile: dict[str, Any]) -> dict[str, Any]:
    """API-only view: owners see plan=owner and effectively unlimited credits."""
    if not is_owner_user(profile):
        return profile
    out = dict(profile)
    used = int(out.get("sessions_used") or 0)
    out["plan"] = "owner"
    out["sessions_limit"] = used + 9999
    return out


def has_sessions_remaining(user_row: dict[str, Any], email: str | None) -> bool:
    if is_owner_user({"email": email}):
        return True
    used = int(user_row.get("sessions_used") or 0)
    limit = int(user_row.get("sessions_limit") or 0)
    return used < limit

"""Merge duplicate product accounts and keep profiles in sync with Supabase Auth."""

from __future__ import annotations

import logging
from typing import Any

from database.supabase_client import supabase_admin
from services.pricing import FREE_PLAN_CREDITS

logger = logging.getLogger(__name__)

PROFILE_FIELDS_TO_PRESERVE = (
    "full_name",
    "college",
    "branch",
    "graduation_year",
    "resume_url",
    "resume_text",
    "target_role",
    "interview_timeline",
)


def _normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def merge_user_data(from_id: str, to_id: str) -> None:
    """Move sessions/reports (and payment orders) from one user row to another."""
    if from_id == to_id:
        return

    supabase_admin.table("sessions").update({"user_id": to_id}).eq("user_id", from_id).execute()
    supabase_admin.table("reports").update({"user_id": to_id}).eq("user_id", from_id).execute()
    try:
        supabase_admin.table("payment_orders").update({"user_id": to_id}).eq("user_id", from_id).execute()
    except Exception:
        pass

    logger.info("Merged user data | from=%s to=%s", from_id, to_id)


def _fill_missing_profile_fields(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field in PROFILE_FIELDS_TO_PRESERVE:
        if not target.get(field) and source.get(field):
            updates[field] = source[field]
    return updates


def reconcile_profile_with_auth(
    profile: dict[str, Any],
    *,
    auth_user_id: str,
    auth_email: str | None,
) -> dict[str, Any]:
    """
    - Sync email from JWT when the row is missing it.
    - If another public.users row shares the same email, merge its data into this auth id.
    """
    email = _normalize_email(auth_email) or _normalize_email(profile.get("email"))
    updates: dict[str, Any] = {}

    if email and _normalize_email(profile.get("email")) != email:
        updates["email"] = email

    if email:
        dupes = (
            supabase_admin.table("users")
            .select("*")
            .eq("email", email)
            .neq("id", auth_user_id)
            .execute()
        )
        for dupe in dupes.data or []:
            merge_user_data(dupe["id"], auth_user_id)
            updates.update(_fill_missing_profile_fields(profile, dupe))
            try:
                supabase_admin.table("users").delete().eq("id", dupe["id"]).execute()
            except Exception as e:
                logger.warning("Could not delete duplicate user row %s: %s", dupe["id"], e)

    if updates:
        result = (
            supabase_admin.table("users")
            .update(updates)
            .eq("id", auth_user_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        merged = dict(profile)
        merged.update(updates)
        return merged

    return profile


def ensure_user_profile(auth_user_id: str, auth_email: str | None) -> dict[str, Any]:
    """Create a public.users row for new auth sign-ups (e.g. Google ID token)."""
    email = _normalize_email(auth_email)
    payload: dict[str, Any] = {
        "id": auth_user_id,
        "email": email or f"{auth_user_id}@users.interviewphodo.local",
        "plan": "free",
        "sessions_used": 0,
        "sessions_limit": FREE_PLAN_CREDITS,
    }
    result = supabase_admin.table("users").insert(payload).execute()
    if not result.data:
        raise RuntimeError(f"Failed to create profile for {auth_user_id}")
    return result.data[0]

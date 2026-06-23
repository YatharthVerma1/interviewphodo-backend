"""Plans, credits, and subscription windows — single source of truth."""

from __future__ import annotations

from typing import Any

VOICE_INTERVIEW_CREDITS = 1
VIDEO_INTERVIEW_CREDITS = 2
FREE_PLAN_CREDITS = 3

PAID_PLAN_IDS = frozenset({"starter", "pro"})
PRO_ONLY_ROUNDS = frozenset({"multi_persona"})

PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_inr": 0,
        "price_paise": 0,
        "credits": FREE_PLAN_CREDITS,
        "access_days": None,
        "billing": None,
        "badge": None,
        "expires": False,
        "features": [
            "3 credits — use anytime, no monthly expiry (for testing the platform)",
            "1 voice interview = 1 credit · 1 video interview = 2 credits",
            "All 8 companies + 6 rounds",
            "Eye-contact & posture detection scoring",
            "Limited progress tracker & charts",
            "Resume upload",
        ],
    },
    "starter": {
        "id": "starter",
        "name": "Starter",
        "price_inr": 399,
        "price_paise": 39900,
        "credits": 11,
        "access_days": 30,
        "billing": "1 month access",
        "badge": "Most Popular",
        "expires": True,
        "features": [
            "1 month access from purchase date",
            "11 credits for the access period",
            "All 8 companies + 6 rounds",
            "Eye-contact & posture detection scoring",
            "Progress tracker & charts",
            "Resume upload & analysis",
            "Priority support",
        ],
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_inr": 1099,
        "price_paise": 109900,
        "credits": 40,
        "access_days": 60,
        "billing": "2 months access",
        "badge": "Best Value",
        "expires": True,
        "features": [
            "2 months access from purchase date",
            "40 credits for the access period",
            "All 8 companies + 6 rounds",
            "Eye-contact & posture detection scoring",
            "Progress tracker & charts",
            "Resume upload & analysis",
            "Priority support",
            "Panel (multi-persona) round",
            "Full simulation mode",
            "ATS resume builder",
        ],
    },
}

PAYMENT_PACKS: dict[str, dict[str, Any]] = {
    "starter": {
        "amount_paise": PLANS["starter"]["price_paise"],
        "credits": PLANS["starter"]["credits"],
        "access_days": PLANS["starter"]["access_days"],
        "plan": "starter",
        "label": (
            f"Starter — ₹{PLANS['starter']['price_inr']} "
            f"({PLANS['starter']['access_days']} days, {PLANS['starter']['credits']} credits)"
        ),
    },
    "pro": {
        "amount_paise": PLANS["pro"]["price_paise"],
        "credits": PLANS["pro"]["credits"],
        "access_days": PLANS["pro"]["access_days"],
        "plan": "pro",
        "label": (
            f"Pro — ₹{PLANS['pro']['price_inr']} "
            f"({PLANS['pro']['access_days']} days, {PLANS['pro']['credits']} credits)"
        ),
    },
}


def plan_config(plan_id: str | None) -> dict[str, Any]:
    key = (plan_id or "free").lower()
    return PLANS.get(key, PLANS["free"])


def plans_for_api() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key in ("free", "starter", "pro"):
        p = dict(PLANS[key])
        p["credit_costs"] = {
            "voice_interview": VOICE_INTERVIEW_CREDITS,
            "video_interview": VIDEO_INTERVIEW_CREDITS,
        }
        out.append(p)
    return out

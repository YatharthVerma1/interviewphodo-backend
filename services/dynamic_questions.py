"""Mid-interview topic injection — fresh questions from company pools + session context."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from prompts.companies import get_company_config

if TYPE_CHECKING:
    from services.interview_fsm import InterviewState


def _session_ai_snippets(state: "InterviewState") -> set[str]:
    snippets: set[str] = set()
    for turn in state.transcript:
        text = (turn.get("ai_text") or "").strip().lower()
        if text:
            snippets.add(text[:120])
    return snippets


def build_mid_interview_injection(state: "InterviewState", count: int = 4) -> str:
    """Pick fresh question themes not yet used this session or in past_topics."""
    config = get_company_config(state.company)
    used = {t.lower().strip() for t in state.past_topics if t}
    used |= _session_ai_snippets(state)

    pools: list[str] = []
    pools.extend(config.get("verbal_technical_questions") or [])
    pools.extend(config.get("behavioral_questions") or [])
    pools.extend(config.get("hr_round_questions") or [])
    pools.extend(config.get("hr_trap_questions") or [])

    fresh: list[str] = []
    shuffled = list(pools)
    random.shuffle(shuffled)
    for theme in shuffled:
        key = theme.lower().strip()[:80]
        if key in used:
            continue
        fresh.append(theme)
        used.add(key)
        if len(fresh) >= count:
            break

    if not fresh:
        fresh = [
            "Ask a deeper follow-up tied to their most recent answer — probe implementation details.",
            "Ask a situational question about teamwork under deadline pressure.",
            "Ask how they would explain a core CS concept to a non-technical manager.",
            "Ask a company-specific motivation question they have not heard yet this session.",
        ]

    lines = "\n".join(f"  • {t}" for t in fresh)
    return (
        "[INTERNAL — MID-INTERVIEW DEPTH INJECTION]\n"
        "The interview must continue until at least 25 minutes total. "
        "Generate completely NEW questions (never repeat earlier topics). "
        "Use these fresh themes as inspiration — rephrase into natural interviewer language:\n"
        f"{lines}\n"
        "Ask ONE question at a time. Wait for the student's answer. "
        "If they ask YOU a question, answer briefly then continue interviewing."
    )

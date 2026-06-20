"""
Company configs and interviewer roster.

Each company exposes the same dict shape (style, tech_focus, question pools,
etc.). On top of that, the centralised INTERVIEWER_ROSTER below holds 3
distinct interviewer personas per company so the SAME company feels like a
DIFFERENT person across sessions — pick_interviewer() picks one at session
start (deterministic seed = session_id, so the persona is stable for the
whole interview but varies across sessions).
"""

import random
from typing import Optional

from .tcs           import TCS_CONFIG
from .infosys       import INFOSYS_CONFIG
from .wipro         import WIPRO_CONFIG
from .hcl           import HCLTEC_CONFIG
from .accenture     import ACCENTURE_CONFIG
from .cognizant     import COGNIZANT_CONFIG
from .tech_mahindra import TECH_MAHINDRA_CONFIG
from .zoho          import ZOHO_CONFIG

COMPANY_CONFIGS = {
    "tcs":           TCS_CONFIG,
    "infosys":       INFOSYS_CONFIG,
    "wipro":         WIPRO_CONFIG,
    "hcl":           HCLTEC_CONFIG,
    "accenture":     ACCENTURE_CONFIG,
    "cognizant":     COGNIZANT_CONFIG,
    "tech_mahindra": TECH_MAHINDRA_CONFIG,
    "zoho":          ZOHO_CONFIG,
}

VALID_COMPANIES = list(COMPANY_CONFIGS.keys())

# Interviewer roster — 3 distinct personas per company.
# Each persona has a `personality` line that shapes Gemini's tone via the
# system prompt, so one TCS interview feels methodical, the next feels
# direct, the next feels conversational.
INTERVIEWER_ROSTER: dict[str, list[dict]] = {
    "tcs": [
        {"name": "Ramesh Iyer",       "role": "Senior HR Manager",
         "personality": "calm, methodical, asks questions slowly and listens carefully"},
        {"name": "Priya Sharma",      "role": "Talent Acquisition Lead",
         "personality": "warm and conversational, but probes deeply when answers feel rehearsed"},
        {"name": "Vikram Subramanian","role": "Engagement Manager",
         "personality": "direct and no-nonsense, expects crisp answers, dislikes filler talk"},
    ],
    "infosys": [
        {"name": "Priya Sharma",      "role": "Talent Acquisition Lead",
         "personality": "structured and process-oriented, follows a textbook interview style"},
        {"name": "Karthik Raghavan",  "role": "Senior Technical Recruiter",
         "personality": "analytical and patient, likes step-by-step thinking"},
        {"name": "Anjali Verma",      "role": "Campus Hiring Manager",
         "personality": "friendly but thorough, likes to discuss real college projects in depth"},
    ],
    "wipro": [
        {"name": "Anjali Nair",       "role": "HR Business Partner",
         "personality": "warm and people-focused, values communication clarity over technical depth"},
        {"name": "Suresh Reddy",      "role": "Technical Lead - Hiring",
         "personality": "practical and grounded, asks how things work in real production scenarios"},
        {"name": "Meena Pillai",      "role": "Senior Recruiter",
         "personality": "energetic and curious, asks lots of follow-up questions"},
    ],
    "hcl": [
        {"name": "Suresh Menon",      "role": "Technical Recruitment Manager",
         "personality": "straight-talking and pragmatic, focuses on what you can ACTUALLY build"},
        {"name": "Divya Krishnan",    "role": "HR Lead - Engineering",
         "personality": "supportive and coaching, helps the candidate frame answers better"},
        {"name": "Arvind Kumar",      "role": "Engineering Manager",
         "personality": "skeptical by default, will challenge weak claims on the resume"},
    ],
    "accenture": [
        {"name": "Meera Krishnan",    "role": "Campus Recruiting Lead",
         "personality": "polished and professional, expects business-like communication"},
        {"name": "Rohan Desai",       "role": "Technical Architect",
         "personality": "intellectual and precise, dislikes vague answers"},
        {"name": "Sneha Patel",       "role": "Senior HR Partner",
         "personality": "high-energy and friendly, makes the candidate feel comfortable but probes hard"},
    ],
    "cognizant": [
        {"name": "Deepak Pillai",     "role": "Technical HR Manager",
         "personality": "balanced and measured, evaluates both technical and soft skills equally"},
        {"name": "Lakshmi Iyer",      "role": "Senior Talent Acquisition",
         "personality": "thoughtful and observational, picks up on body language cues"},
        {"name": "Manoj Bhat",        "role": "Delivery Manager",
         "personality": "outcome-focused, wants concrete examples of what you delivered"},
    ],
    "tech_mahindra": [
        {"name": "Vikram Rao",        "role": "Talent Acquisition Specialist",
         "personality": "casual and friendly, likes natural conversation"},
        {"name": "Pooja Deshmukh",    "role": "Technical HR",
         "personality": "structured and checklist-driven, covers each topic systematically"},
        {"name": "Sanjay Kulkarni",   "role": "Practice Lead",
         "personality": "curious about real-world thinking, asks 'how would you handle X' a lot"},
    ],
    "zoho": [
        {"name": "Anand Krishnan",    "role": "Senior Engineer and Interviewer",
         "personality": "deeply technical, expects original thinking, dislikes textbook answers"},
        {"name": "Lakshmi Narayanan", "role": "Engineering Lead",
         "personality": "patient and Socratic, will guide the student through hard problems with hints"},
        {"name": "Rajesh Pandian",    "role": "Senior Software Engineer",
         "personality": "blunt and tough, raises the bar quickly when student answers well"},
    ],
}


def get_company_config(company_id: str) -> dict:
    config = COMPANY_CONFIGS.get(company_id.lower())
    if not config:
        raise ValueError(
            f"Unknown company '{company_id}'. Valid options: {VALID_COMPANIES}"
        )
    return config


def pick_interviewer(company_id: str, seed: Optional[str] = None) -> dict:
    """Pick one interviewer persona for this session.

    `seed` should be the session_id (or anything stable per session). Same
    seed → same persona for the whole interview. Different sessions → likely
    different persona, so the SAME company feels like a different person
    across attempts.
    """
    roster = INTERVIEWER_ROSTER.get(company_id.lower())
    if not roster:
        # Fall back to whatever the company config has hard-coded
        cfg = get_company_config(company_id)
        return {
            "name":        cfg.get("interviewer_name", "Interviewer"),
            "role":        cfg.get("interviewer_role", "Hiring Manager"),
            "personality": "professional and balanced",
        }
    rng = random.Random(seed) if seed else random
    return rng.choice(roster)


# Heuristic role tags — used when assembling a multi-persona panel so we can
# pick a "technical-leaning" person for the TECHNICAL phase and an
# "HR/manager-leaning" person for the HR phase. Falls back to round-robin
# if the heuristics don't match.
_ROLE_KEYWORDS_TECHNICAL = (
    "engineer", "tech lead", "tech ", "engineering", "architect",
    "delivery", "practice lead", "manager - hiring",
)
_ROLE_KEYWORDS_HR = (
    "hr", "talent", "recruit", "campus", "people", "partner",
)


def _role_lean(role: str) -> str:
    r = role.lower()
    if any(kw in r for kw in _ROLE_KEYWORDS_TECHNICAL):
        return "technical"
    if any(kw in r for kw in _ROLE_KEYWORDS_HR):
        return "hr"
    return "mixed"


def pick_multi_personas(company_id: str, seed: Optional[str] = None) -> dict:
    """Build a 3-person panel for a multi_persona round.

    Returns a dict mapping the 'role slot' to a chosen persona:
        {
          "warmup":    {...},  # opens INTRO + RESUME
          "technical": {...},  # runs TECHNICAL + BEHAVIORAL
          "hr":        {...},  # runs HR_ROUND + CANDIDATE_QA + CLOSING
        }

    Strategy: pick a 'technical-leaning' persona for the technical slot, an
    'HR-leaning' persona for the HR slot, and any remaining persona for
    warmup. If the company's 3-person roster doesn't cleanly split, falls
    back to a deterministic round-robin keyed on `seed`.
    """
    roster = INTERVIEWER_ROSTER.get(company_id.lower(), [])
    if not roster:
        single = pick_interviewer(company_id, seed)
        return {"warmup": single, "technical": single, "hr": single}

    rng = random.Random(seed) if seed else random
    pool = list(roster)
    rng.shuffle(pool)

    by_lean: dict[str, list[dict]] = {"technical": [], "hr": [], "mixed": []}
    for p in pool:
        by_lean[_role_lean(p.get("role", ""))].append(p)

    def _pop(category: str) -> Optional[dict]:
        if by_lean[category]:
            return by_lean[category].pop(0)
        # Fallback: borrow from another category
        for fallback in ("mixed", "technical", "hr"):
            if by_lean[fallback]:
                return by_lean[fallback].pop(0)
        return None

    technical = _pop("technical") or pool[0]
    hr        = _pop("hr")        or pool[-1]
    warmup    = _pop("mixed")     or _pop("technical") or _pop("hr") or pool[0]

    return {"warmup": warmup, "technical": technical, "hr": hr}


# Phase → which persona slot speaks for it during a multi_persona round.
PHASE_TO_PERSONA_SLOT = {
    "intro":         "warmup",
    "resume_review": "warmup",
    "technical_qa":  "technical",
    "behavioral":    "technical",
    "hr_round":      "hr",
    "candidate_qa":  "hr",
    "closing":       "hr",
}


def build_personas_by_phase(panel: dict) -> dict:
    """Expand a 3-slot panel ({warmup,technical,hr}) into a full
    {phase_value: persona} map that the FSM can index per phase."""
    return {
        phase_value: panel.get(slot, panel.get("warmup"))
        for phase_value, slot in PHASE_TO_PERSONA_SLOT.items()
    }

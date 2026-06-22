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

# Interviewer roster — distinct personas per company.
# `lean` controls which round types each persona may run (see pick_interviewer_for_round):
#   hr          → HR round (Round 6)
#   technical   → Technical round (Round 2-3)
#   managerial  → Managerial / behavioral round (Round 5)
INTERVIEWER_ROSTER: dict[str, list[dict]] = {
    "tcs": [
        {"name": "Ramesh Iyer",        "role": "Senior HR Manager",
         "lean": "hr",
         "personality": "calm, methodical, asks questions slowly and listens carefully"},
        {"name": "Priya Sharma",       "role": "Talent Acquisition Lead",
         "lean": "hr",
         "personality": "warm and conversational, but probes deeply when answers feel rehearsed"},
        {"name": "Vikram Subramanian", "role": "Engagement Manager",
         "lean": "managerial",
         "personality": "direct and no-nonsense, expects crisp answers, dislikes filler talk"},
        {"name": "Karthik Menon",      "role": "Technical Lead — Campus Hiring",
         "lean": "technical",
         "personality": "structured technical interviewer — DSA, core CS, and project depth; not an HR round"},
    ],
    "infosys": [
        {"name": "Priya Sharma",       "role": "Talent Acquisition Lead",
         "lean": "hr",
         "personality": "structured and process-oriented, follows a textbook HR interview style"},
        {"name": "Karthik Raghavan",   "role": "Senior Technical Recruiter",
         "lean": "hr",
         "personality": "HR-facing recruiter who runs Round 6 — salary, bond, career goals; not a coding interviewer"},
        {"name": "Anjali Verma",       "role": "Campus Hiring Manager",
         "lean": "managerial",
         "personality": "friendly but thorough, situational and behavioral focus, likes real college project stories"},
        {"name": "Rohan Das",          "role": "Senior Technical Interviewer",
         "lean": "technical",
         "personality": "analytical and patient, expects step-by-step technical explanations"},
    ],
    "wipro": [
        {"name": "Anjali Nair",        "role": "HR Business Partner",
         "lean": "hr",
         "personality": "warm and people-focused, values communication clarity over technical depth"},
        {"name": "Suresh Reddy",       "role": "Technical Lead — Hiring",
         "lean": "technical",
         "personality": "practical and grounded, asks how things work in real production scenarios"},
        {"name": "Meena Pillai",       "role": "Senior Recruiter",
         "lean": "hr",
         "personality": "energetic HR interviewer, covers CTC, relocation, and India-specific traps"},
        {"name": "Rajesh Nambiar",     "role": "Delivery Manager",
         "lean": "managerial",
         "personality": "outcome-focused managerial interviewer, STAR behavioral and leadership scenarios"},
    ],
    "hcl": [
        {"name": "Suresh Menon",       "role": "Technical Recruitment Manager",
         "lean": "technical",
         "personality": "straight-talking technical interviewer, focuses on what you can ACTUALLY build"},
        {"name": "Divya Krishnan",     "role": "HR Lead — Engineering",
         "lean": "hr",
         "personality": "supportive HR interviewer, career goals, compensation, and background checks"},
        {"name": "Arvind Kumar",       "role": "Engineering Manager",
         "lean": "managerial",
         "personality": "skeptical hiring manager, challenges weak resume claims with situational questions"},
        {"name": "Neha Gupta",         "role": "Senior Software Engineer — Interviewer",
         "lean": "technical",
         "personality": "deep technical probes on DSA, systems, and project implementation"},
    ],
    "accenture": [
        {"name": "Meera Krishnan",     "role": "Campus Recruiting Lead",
         "lean": "hr",
         "personality": "polished HR interviewer, expects business-like communication on career and fit"},
        {"name": "Rohan Desai",        "role": "Technical Architect",
         "lean": "technical",
         "personality": "intellectual and precise technical interviewer, dislikes vague answers"},
        {"name": "Sneha Patel",        "role": "Senior HR Partner",
         "lean": "hr",
         "personality": "high-energy HR round, makes candidate comfortable but probes hard on motivation"},
        {"name": "Amit Shah",          "role": "Associate Manager — Hiring",
         "lean": "managerial",
         "personality": "managerial round focus — consulting scenarios, teamwork, client handling"},
    ],
    "cognizant": [
        {"name": "Deepak Pillai",      "role": "Technical HR Manager",
         "lean": "hr",
         "personality": "HR round specialist — evaluates motivation and fit, not DSA or coding"},
        {"name": "Lakshmi Iyer",       "role": "Senior Talent Acquisition",
         "lean": "hr",
         "personality": "thoughtful HR interviewer, relocation, CTC, and notice-period traps"},
        {"name": "Manoj Bhat",         "role": "Delivery Manager",
         "lean": "managerial",
         "personality": "managerial interviewer, wants concrete delivery and ownership examples"},
        {"name": "Sanjay Rao",         "role": "Technical Lead — Engineering",
         "lean": "technical",
         "personality": "balanced technical depth — verbal DSA, core CS, and project walkthroughs"},
    ],
    "tech_mahindra": [
        {"name": "Vikram Rao",         "role": "Talent Acquisition Specialist",
         "lean": "hr",
         "personality": "casual HR interviewer, natural conversation on career and compensation"},
        {"name": "Pooja Deshmukh",     "role": "Technical HR",
         "lean": "hr",
         "personality": "structured HR round, checklist on bond, location, and long-term fit"},
        {"name": "Sanjay Kulkarni",    "role": "Practice Lead",
         "lean": "technical",
         "personality": "technical interviewer, real-world problem solving and system thinking"},
        {"name": "Meera Joshi",        "role": "Senior Manager — Campus Hiring",
         "lean": "managerial",
         "personality": "managerial round, leadership stories and conflict-resolution scenarios"},
    ],
    "zoho": [
        {"name": "Anand Krishnan",     "role": "Senior Engineer and Interviewer",
         "lean": "technical",
         "personality": "deeply technical, expects original thinking, dislikes textbook answers"},
        {"name": "Lakshmi Narayanan",  "role": "Engineering Lead",
         "lean": "technical",
         "personality": "patient technical interviewer, Socratic hints on hard problems"},
        {"name": "Rajesh Pandian",     "role": "Senior Software Engineer",
         "lean": "technical",
         "personality": "tough technical bar, raises difficulty when student answers well"},
        {"name": "Priya Venkatesh",    "role": "Senior HR Manager — Campus Hiring",
         "lean": "hr",
         "personality": "warm HR interviewer — CTC, bond, relocation, motivation; never runs DSA rounds"},
        {"name": "Vikram Iyer",        "role": "Engineering Manager",
         "lean": "managerial",
         "personality": "managerial round — product ownership, depth vs breadth, team fit at Zoho"},
    ],
}


def get_company_config(company_id: str) -> dict:
    from .pool_extensions import merge_pool_extensions

    config = COMPANY_CONFIGS.get(company_id.lower())
    if not config:
        raise ValueError(
            f"Unknown company '{company_id}'. Valid options: {VALID_COMPANIES}"
        )
    return merge_pool_extensions(config)


def pick_interviewer(company_id: str, seed: Optional[str] = None) -> dict:
    """Pick one interviewer persona for this session (random from roster)."""
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


# Persona classification — explicit `lean` on roster entries is authoritative.
_ROLE_KEYWORDS_TECHNICAL = (
    "senior engineer", "software engineer", "engineering lead", "technical lead",
    "technical architect", "tech lead", "sde",
)
_ROLE_KEYWORDS_HR = (
    "hr", "human resources", "talent acquisition", "recruiter", "recruiting",
    "campus hiring", "people partner", "business partner",
)
_ROLE_KEYWORDS_MANAGERIAL = (
    "engagement manager", "delivery manager", "engineering manager",
    "hiring manager", "practice lead", "associate manager",
)


def _persona_lean(persona: dict) -> str:
    explicit = (persona.get("lean") or "").lower().strip()
    if explicit in ("hr", "technical", "managerial"):
        return explicit
    return _role_lean_from_title(persona.get("role", ""))


def _role_lean_from_title(role: str) -> str:
    r = role.lower()
    if any(kw in r for kw in _ROLE_KEYWORDS_HR):
        return "hr"
    if any(kw in r for kw in _ROLE_KEYWORDS_TECHNICAL):
        return "technical"
    if any(kw in r for kw in _ROLE_KEYWORDS_MANAGERIAL):
        return "managerial"
    return "mixed"


def _role_lean(role: str) -> str:
    """Backward-compat wrapper for title-only classification."""
    return _role_lean_from_title(role)


def _synthetic_technical_persona(company_id: str, seed: Optional[str] = None) -> dict:
    cfg = get_company_config(company_id)
    rng = random.Random(f"{seed}:tech" if seed else None)
    names = ["Karthik Menon", "Rohan Das", "Suresh Reddy", "Anand Krishnan", "Neha Gupta"]
    return {
        "name": rng.choice(names),
        "role": f"Technical Interviewer — {cfg['company_name']} Engineering",
        "lean": "technical",
        "personality": (
            "technical round interviewer — verbal DSA, core CS, system thinking, and deep "
            "project probes. Does NOT conduct HR or salary discussions."
        ),
    }


def _synthetic_hr_persona(company_id: str, seed: Optional[str] = None) -> dict:
    cfg = get_company_config(company_id)
    rng = random.Random(f"{seed}:hr" if seed else None)
    names = ["Priya Venkatesh", "Meera Shah", "Kavitha Reddy", "Ananya Iyer"]
    return {
        "name": rng.choice(names),
        "role": f"HR Manager — {cfg['company_name']} Campus Hiring",
        "lean": "hr",
        "personality": (
            "professional HR interviewer for Round 6 — career goals, CTC, bond, relocation, "
            "notice period, and India-specific trap questions. Does NOT conduct technical, DSA, "
            "or coding interviews."
        ),
    }


def _synthetic_managerial_persona(company_id: str, seed: Optional[str] = None) -> dict:
    cfg = get_company_config(company_id)
    rng = random.Random(f"{seed}:mgr" if seed else None)
    names = ["Vikram Menon", "Sanjay Kulkarni", "Arun Mehta", "Deepa Nair"]
    return {
        "name": rng.choice(names),
        "role": f"Hiring Manager — {cfg['company_name']}",
        "lean": "managerial",
        "personality": (
            "managerial round interviewer — situational judgment, leadership, project ownership, "
            "STAR behavioral stories. Minimal technical depth; not a DSA or coding round."
        ),
    }


_ROUND_TO_LEAN = {
    "hr": "hr",
    "technical": "technical",
    "managerial": "managerial",
}


def pick_interviewer_for_round(
    company_id: str,
    round_type: str,
    seed: Optional[str] = None,
) -> dict:
    """Pick a persona that matches the round the student selected."""
    rt = (round_type or "full").lower().strip()
    if rt == "mixed":
        rt = "full"

    roster = INTERVIEWER_ROSTER.get(company_id.lower(), [])
    rng = random.Random(seed) if seed else random

    target_lean = _ROUND_TO_LEAN.get(rt)
    if target_lean:
        pool = [p for p in roster if _persona_lean(p) == target_lean]
        if pool:
            return rng.choice(pool)
        if target_lean == "hr":
            return _synthetic_hr_persona(company_id, seed)
        if target_lean == "technical":
            return _synthetic_technical_persona(company_id, seed)
        if target_lean == "managerial":
            return _synthetic_managerial_persona(company_id, seed)

    return pick_interviewer(company_id, seed)


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

    by_lean: dict[str, list[dict]] = {"technical": [], "hr": [], "managerial": [], "mixed": []}
    for p in pool:
        lean = _persona_lean(p)
        bucket = lean if lean in by_lean else "mixed"
        by_lean[bucket].append(p)

    def _pop(category: str) -> Optional[dict]:
        if by_lean[category]:
            return by_lean[category].pop(0)
        for fallback in ("mixed", "managerial", "technical", "hr"):
            if by_lean[fallback]:
                return by_lean[fallback].pop(0)
        return None

    technical = _pop("technical") or _synthetic_technical_persona(company_id, seed)
    hr        = _pop("hr")        or _synthetic_hr_persona(company_id, seed)
    warmup    = _pop("managerial") or _pop("mixed") or _pop("hr") or technical

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

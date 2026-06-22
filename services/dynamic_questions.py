"""Mid-interview question injection — Gemini-generated + company pool fallback.

Works for ALL companies (via get_company_config) and ALL round types.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import TYPE_CHECKING, Optional

from config import settings
from prompts.companies import get_company_config
from services.interview_fsm import InterviewPhase

if TYPE_CHECKING:
    from services.interview_fsm import InterviewState

logger = logging.getLogger(__name__)

_TEXT_MODEL = "gemini-2.0-flash"

# Every phase that asks questions gets Gemini injection (not intro/closing).
PHASES_WITH_GEMINI_INJECTION = frozenset({
    InterviewPhase.RESUME,
    InterviewPhase.TECHNICAL,
    InterviewPhase.BEHAVIORAL,
    InterviewPhase.HR_ROUND,
    InterviewPhase.CANDIDATE_QA,
})

_PHASE_THEMES: dict[InterviewPhase, tuple[str, ...]] = {
    InterviewPhase.RESUME: ("verbal_technical_questions", "behavioral_questions"),
    InterviewPhase.TECHNICAL: ("verbal_technical_questions",),
    InterviewPhase.BEHAVIORAL: ("behavioral_questions",),
    InterviewPhase.HR_ROUND: ("hr_round_questions", "hr_trap_questions"),
    InterviewPhase.CANDIDATE_QA: ("hr_round_questions",),
}

_PHASE_GENERATION_HINTS = {
    InterviewPhase.RESUME: (
        "resume-based questions about projects, internships, skills, and academics — "
        "probe one bullet on their resume deeply"
    ),
    InterviewPhase.TECHNICAL: (
        "verbal technical questions (DSA, OOP, DBMS, OS, projects) — no live coding"
    ),
    InterviewPhase.BEHAVIORAL: (
        "behavioral / STAR situational questions tied to teamwork, leadership, conflict, pressure"
    ),
    InterviewPhase.HR_ROUND: (
        "India-specific HR questions including bond, relocation, CTC, why this company, "
        "plus one realistic trap-question variation"
    ),
    InterviewPhase.CANDIDATE_QA: (
        "topics the student could ask the interviewer about the company, role, and growth — "
        "use these to coach them on good questions if they have none"
    ),
}

_ROUND_TYPE_CONTEXT = {
    "technical": "Round 2-3 technical interview — heavy DSA and core CS depth.",
    "managerial": "Round 5 managerial interview — leadership, ownership, situational depth.",
    "hr": "Round 6 HR interview — salary, career, India trap questions.",
    "full": "Full mock — all phases, must run 25+ minutes with balanced depth.",
    "coaching": "Coaching session — teach frameworks, then ask follow-up attempts.",
    "multi_persona": "Panel interview — three interviewers, stay in character per phase.",
    "mixed": "Full mock — all phases, must run 25+ minutes with balanced depth.",
}


def phase_accepts_gemini_injection(phase: InterviewPhase) -> bool:
    return phase in PHASES_WITH_GEMINI_INJECTION


def _question_count_for_phase(state: "InterviewState", phase: InterviewPhase) -> int:
    """How many fresh themes to generate — scales with phase budget and round type."""
    budget = state.get_phase_budget(phase)
    if phase == InterviewPhase.CANDIDATE_QA:
        return min(8, max(4, budget // 2))
    if state.round_type == "coaching":
        return min(8, max(5, budget // 4))
    return min(8, max(5, budget // 3))


def _session_ai_snippets(state: "InterviewState") -> set[str]:
    snippets: set[str] = set()
    for turn in state.transcript:
        text = (turn.get("ai_text") or "").strip().lower()
        if text:
            snippets.add(text[:120])
    return snippets


def _recent_student_context(state: "InterviewState", max_chars: int = 600) -> str:
    bits: list[str] = []
    for turn in state.transcript[-6:]:
        ans = (turn.get("student_text") or "").strip()
        if ans:
            bits.append(ans[:200])
    joined = " | ".join(bits)
    return joined[:max_chars] or "No prior answers yet."


def _pool_for_phase(config: dict, phase: InterviewPhase) -> list[str]:
    pools: list[str] = []
    for key in _PHASE_THEMES.get(phase, ()):
        pools.extend(config.get(key) or [])
    return pools


def _pick_pool_themes(
    state: "InterviewState",
    phase: InterviewPhase,
    count: int,
) -> list[str]:
    config = get_company_config(state.company)
    used = {t.lower().strip() for t in state.past_topics if t}
    used |= _session_ai_snippets(state)

    fresh: list[str] = []
    shuffled = list(_pool_for_phase(config, phase))
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
        fresh = _generic_fallback_themes(phase, count, config)
    return fresh


def _generic_fallback_themes(phase: InterviewPhase, count: int, config: dict) -> list[str]:
    company = config.get("company_name", "the company")
    tech = config.get("tech_focus", "core CS and projects")
    generic = {
        InterviewPhase.RESUME: [
            f"Deep dive into one project on their resume — tech stack and their personal contribution.",
            f"Ask about a skill on their resume and how they used it in a real task.",
            f"Challenge a claim on their resume with a follow-up 'how exactly did you implement that?'",
        ],
        InterviewPhase.TECHNICAL: [
            f"Core concept from {tech} tied to something they mentioned earlier.",
            "Deep follow-up on their most recent project — architecture and trade-offs.",
            "Problem-solving approach for a scalability scenario in their stack.",
            "Explain time/space complexity of a structure they chose in a project.",
        ],
        InterviewPhase.BEHAVIORAL: [
            "STAR story about conflict with a teammate on a deadline.",
            "Time they took initiative without being asked.",
            "Handling failure or a bug that reached production.",
            f"Why they want to work at {company} — behavioral angle, not HR salary talk.",
        ],
        InterviewPhase.HR_ROUND: [
            f"Why {company} over competitors — strategic honest answer.",
            "Relocation and bond willingness — India context.",
            "Salary expectation framing for a fresher.",
            "Trap-style question about joining a competitor after training.",
        ],
        InterviewPhase.CANDIDATE_QA: [
            f"What does the first 6 months look like for a fresher at {company}?",
            "How does the company support learning and mentorship?",
        ],
    }
    items = list(generic.get(phase, generic[InterviewPhase.TECHNICAL]))
    random.shuffle(items)
    return items[:count]


def _parse_numbered_questions(text: str, limit: int) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: list[str] = []
    for ln in lines:
        cleaned = re.sub(r"^[\d\.\)\-\*]+\s*", "", ln).strip()
        if len(cleaned) < 20:
            continue
        if cleaned.endswith("?"):
            out.append(cleaned)
        elif "?" in cleaned:
            out.append(cleaned.split("?")[0].strip() + "?")
        else:
            out.append(cleaned)
        if len(out) >= limit:
            break
    return out


def _generate_questions_sync(
    state: "InterviewState",
    phase: InterviewPhase,
    count: int,
) -> list[str]:
    if not settings.google_api_key:
        return []

    hint = _PHASE_GENERATION_HINTS.get(phase, "interview questions")
    config = get_company_config(state.company)
    resume = (state.resume_text or "No resume provided")[:800]
    recent = _recent_student_context(state)
    asked = "\n".join(f"- {s[:100]}" for s in list(_session_ai_snippets(state))[:12])
    round_ctx = _ROUND_TYPE_CONTEXT.get(state.round_type, "placement mock interview")

    prompt = f"""You are helping an Indian BTech placement interview coach.

Company: {config.get('company_name', state.company)}
Company interview style: {config.get('style', '')[:400]}
Company tech focus: {config.get('tech_focus', '')[:400]}
Round type: {state.round_type} — {round_ctx}
Current interview phase: {phase.value}
Target role: {state.target_role or 'general software engineer'}

Student resume excerpt:
{resume}

Recent student answers this session:
{recent}

Questions/themes ALREADY used this session (do NOT repeat):
{asked or '(none yet)'}

Generate exactly {count} fresh, logical {hint} specific to {config.get('company_name', state.company)}.
Rules:
- Each question must be ONE complete interview question ending with ?
- Tie at least half of them to the student's resume or recent answers when possible
- Reflect this company's known interview style and focus areas
- Do NOT copy verbatim from generic lists — original wording only
- Number each line 1-{count}
- Output ONLY the numbered questions, no preamble
"""

    try:
        from google import genai

        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model=_TEXT_MODEL,
            contents=prompt,
        )
        raw = (response.text or "").strip()
        parsed = _parse_numbered_questions(raw, count)
        if parsed:
            logger.info(
                f"Gemini generated {len(parsed)} {phase.value} questions | "
                f"company={state.company} round={state.round_type} session={state.session_id}"
            )
        return parsed
    except Exception as e:
        logger.warning(f"Gemini question generation failed: {e}")
        return []


async def generate_fresh_questions(
    state: "InterviewState",
    phase: Optional[InterviewPhase] = None,
    count: int = 6,
) -> list[str]:
    """Ask Gemini (text API) for new questions; fall back to company pools."""
    target = phase or state.current_phase
    generated = await asyncio.to_thread(_generate_questions_sync, state, target, count)
    if generated:
        return generated
    return _pick_pool_themes(state, target, count)


def _format_injection(
    state: "InterviewState",
    themes: list[str],
    *,
    phase: Optional[InterviewPhase] = None,
    header: str,
) -> str:
    phase = phase or state.current_phase
    remaining = max(1, state.get_phase_budget(phase) - state.phase_turn)
    lines = "\n".join(f"  • {t}" for t in themes)
    config = get_company_config(state.company)
    return (
        f"{header}\n"
        f"Company: {config.get('company_name', state.company)} | "
        f"Round: {state.round_type} | "
        f"Phase: {phase.value.replace('_', ' ')} | "
        f"Student answers in this phase: {state.phase_turn} | "
        f"Minimum remaining in this phase: {remaining}\n"
        "Generate completely NEW questions in natural spoken language — "
        "do NOT read these bullet points verbatim. Use them as inspiration only:\n"
        f"{lines}\n"
        "Ask ONE question at a time. Wait for a substantive student answer. "
        "Do NOT tell the student to disconnect or that your time is up. "
        "The interview must continue until at least 25 minutes total."
    )


async def build_phase_start_injection(state: "InterviewState") -> str:
    """Fresh Gemini questions when entering any question phase (all companies/rounds)."""
    phase = state.current_phase
    if not phase_accepts_gemini_injection(phase):
        return ""
    count = _question_count_for_phase(state, phase)
    themes = await generate_fresh_questions(state, phase, count=count)
    return _format_injection(
        state,
        themes,
        phase=phase,
        header="[INTERNAL — NEW PHASE QUESTION BANK]",
    )


async def build_mid_interview_injection(
    state: "InterviewState",
    count: Optional[int] = None,
    *,
    use_gemini_api: bool = False,
) -> str:
    """Pick fresh question themes for the active phase.

    Default is instant pool selection — async Gemini text API calls block the
    live audio path for 1–3s and make the interviewer sound stuck.
    """
    phase = state.current_phase
    if count is None:
        count = max(4, _question_count_for_phase(state, phase) // 2)
    if use_gemini_api:
        themes = await generate_fresh_questions(state, phase, count=count)
    else:
        themes = _pick_pool_themes(state, phase, count)
    return _format_injection(
        state,
        themes,
        header="[INTERNAL — MID-INTERVIEW DEPTH INJECTION]",
    )

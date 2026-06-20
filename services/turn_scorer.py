"""
Per-turn scoring and feedback — interviewphodo.com

After each student answer, we produce:
  - score (1-10)
  - feedback (1-2 sentences explaining why)

Strategy (in priority order):
  1. Parse [SCORE:N] tag if the AI included one in its spoken response
  2. Parse common spoken patterns ("7 out of 10", "I'd rate that a 6")
  3. Fall back to heuristic scoring from answer quality signals
"""

from __future__ import annotations

import re
from typing import Optional

# Phases where we skip scoring (intro warm-up, closing report, candidate Q&A)
_SKIP_PHASES = frozenset({"intro", "candidate_qa", "closing"})

_SCORE_TAG_RE = re.compile(r"\[SCORE:\s*(\d{1,2})\s*\]", re.IGNORECASE)
_SPOKEN_SCORE_RES = [
    re.compile(r"(\d{1,2})\s*/\s*10", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s+out\s+of\s+10", re.IGNORECASE),
    re.compile(r"rate(?:d)?\s+(?:that|this|your\s+answer)?\s*(?:a|at)?\s*(\d{1,2})", re.IGNORECASE),
    re.compile(r"score\s+(?:of|is|:)\s*(\d{1,2})", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s+out\s+of\s+ten", re.IGNORECASE),
]

_STAR_KEYWORDS = (
    "situation", "task", "action", "result",
    "when i", "my team", "i led", "i implemented", "we delivered",
)

_TECH_KEYWORDS = (
    "complexity", "algorithm", "data structure", "oop", "class", "object",
    "database", "sql", "index", "hash", "tree", "graph", "stack", "queue",
    "time complexity", "space complexity", "recursion", "api", "system",
)


def score_turn(
    phase: str,
    student_text: str,
    ai_text: str,
    filler_words: Optional[list] = None,
) -> tuple[Optional[int], str]:
    """Return (score 1-10 or None, feedback string) for one interview turn."""
    fillers = filler_words or []
    student = (student_text or "").strip()
    ai = (ai_text or "").strip()

    if phase in _SKIP_PHASES:
        return None, ""

    if not student:
        return 2, "No answer detected — in a real interview, always attempt an answer rather than staying silent."

    score = _parse_score_from_ai(ai)
    feedback = _extract_feedback(ai, score)

    if score is None:
        score = _heuristic_score(phase, student, fillers)
        if not feedback:
            feedback = _heuristic_feedback(phase, student, fillers, score)

    score = max(1, min(10, score))
    if not feedback:
        feedback = _heuristic_feedback(phase, student, fillers, score)

    # Strip score tags from feedback shown to the student
    feedback = _SCORE_TAG_RE.sub("", feedback).strip()
    return score, feedback


def build_turn_breakdown(transcript: list) -> list[dict]:
    """Build a frontend-friendly per-turn list from the session transcript."""
    breakdown = []
    for t in transcript:
        phase = t.get("phase", "")
        if phase in _SKIP_PHASES:
            continue
        score = t.get("score")
        if score is None:
            continue
        breakdown.append({
            "turn":           t.get("turn"),
            "phase":          phase,
            "score":          score,
            "feedback":       t.get("feedback") or "",
            "student_preview": _preview(t.get("student_text", ""), 120),
            "ai_preview":     _preview(t.get("ai_text", ""), 80),
            "filler_count":   len(t.get("filler_words") or []),
        })
    return breakdown


def _parse_score_from_ai(ai_text: str) -> Optional[int]:
    m = _SCORE_TAG_RE.search(ai_text)
    if m:
        return int(m.group(1))
    for pat in _SPOKEN_SCORE_RES:
        m = pat.search(ai_text)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return val
    return None


def _extract_feedback(ai_text: str, score: Optional[int]) -> str:
    """Pull the evaluation sentences from the AI response (before the next question)."""
    if not ai_text:
        return ""

    text = _SCORE_TAG_RE.sub("", ai_text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if not sentences:
        return ""

    # Evaluation usually comes before the last sentence (which is often the next question)
    eval_parts: list[str] = []
    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        # Stop collecting once we hit a clear new question
        if s.endswith("?") and len(eval_parts) >= 1:
            break
        eval_parts.append(s)

    if not eval_parts:
        return sentences[0][:200] if sentences else ""

    # If only one sentence and it's a question, no real feedback was given
    if len(eval_parts) == 1 and eval_parts[0].endswith("?"):
        return ""

    # Drop trailing question sentence if present
    if eval_parts and eval_parts[-1].endswith("?"):
        eval_parts = eval_parts[:-1]

    feedback = " ".join(eval_parts).strip()
    return feedback[:300] if feedback else ""


def _heuristic_score(phase: str, student_text: str, fillers: list) -> int:
    words = student_text.split()
    word_count = len(words)
    score = 5  # baseline

    # Length signals
    if word_count < 15:
        score -= 2
    elif word_count < 30:
        score -= 1
    elif word_count >= 60:
        score += 1
    elif word_count >= 100:
        score += 2

    # Filler penalty
    filler_penalty = min(3, len(fillers))
    score -= filler_penalty

    # Phase-specific bonuses
    lower = student_text.lower()
    if phase == "behavioral":
        star_hits = sum(1 for kw in _STAR_KEYWORDS if kw in lower)
        score += min(2, star_hits)
    elif phase == "technical_qa":
        tech_hits = sum(1 for kw in _TECH_KEYWORDS if kw in lower)
        score += min(2, tech_hits)
    elif phase == "hr_round":
        if any(w in lower for w in ("company", "career", "learn", "grow", "relocate", "team")):
            score += 1
    elif phase == "resume_review":
        if any(w in lower for w in ("project", "built", "developed", "implemented", "team", "my role")):
            score += 1

    # Vague answer penalty
    if word_count > 10 and any(
        phrase in lower
        for phrase in ("i don't know", "not sure", "no idea", "cannot say", "can't say")
    ):
        score -= 2

    return max(1, min(10, score))


def _heuristic_feedback(phase: str, student_text: str, fillers: list, score: int) -> str:
    words = student_text.split()
    word_count = len(words)
    parts: list[str] = []

    if score >= 8:
        parts.append("Strong answer — clear, specific, and well-structured.")
    elif score >= 6:
        parts.append("Decent answer — you covered the basics but could go deeper.")
    elif score >= 4:
        parts.append("Average answer — needs more specific examples and structure.")
    else:
        parts.append("Weak answer — too brief or vague for a real interview.")

    if word_count < 20:
        parts.append("Try to elaborate with a concrete example from your projects or college work.")
    if len(fillers) >= 3:
        parts.append(f"You used {len(fillers)} filler words — pause silently instead of saying 'um' or 'basically'.")

    if phase == "behavioral":
        parts.append("Use the STAR format: Situation → Task → Action → Result.")
    elif phase == "technical_qa":
        parts.append("Structure technical answers: definition → how it works → example → trade-offs.")
    elif phase == "hr_round":
        parts.append("Be honest but strategic — acknowledge the concern, then reframe positively.")

    return " ".join(parts[:2])


def _preview(text: str, max_len: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."

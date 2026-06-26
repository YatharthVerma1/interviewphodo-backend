"""Interview analysis helpers — STAR scoring, delivery metrics, progress insights."""

from __future__ import annotations

from collections import defaultdict

STAR_SITUATION = (
    "when", "during", "at my", "project", "company", "team", "intern",
    "college", "university", "semester", "role", "worked at", "while",
)
STAR_TASK = (
    "task", "goal", "challenge", "problem", "needed", "responsible",
    "assigned", "objective", "required", "deadline",
)
STAR_ACTION = (
    "i built", "i created", "i implemented", "i led", "i developed",
    "i worked", "i designed", "i solved", "i wrote", "i managed",
    "we built", "we created", "i used", "i applied",
)
STAR_RESULT = (
    "result", "outcome", "improved", "reduced", "increased", "achieved",
    "learned", "saved", "successfully", "impact", "delivered", "completed",
    "%", "percent", "growth", "performance",
)

_BEHAVIORAL_PHASES = frozenset({"behavioral", "hr_round", "resume_review", "managerial"})

_SKILL_LABELS = {
    "technical": "Technical Q&A",
    "communication": "Communication",
    "behavioral": "Behavioral answers",
    "hr_strategy": "HR & strategy",
}


def _keyword_score(text: str, keywords: tuple[str, ...]) -> int:
    lower = (text or "").lower()
    if not lower.strip():
        return 0
    hits = sum(1 for kw in keywords if kw in lower)
    if hits >= 3:
        return 9
    if hits >= 2:
        return 7
    if hits >= 1:
        return 5
    return 2


def analyse_star_text(text: str) -> dict:
    """Score one answer for STAR structure (each dimension 0–10)."""
    situation = _keyword_score(text, STAR_SITUATION)
    task = _keyword_score(text, STAR_TASK)
    action = _keyword_score(text, STAR_ACTION)
    result = _keyword_score(text, STAR_RESULT)
    dims = [situation, task, action, result]
    overall = round(sum(dims) / len(dims), 1) if dims else 0.0

    missing = []
    if situation < 5:
        missing.append("Situation")
    if task < 5:
        missing.append("Task")
    if action < 5:
        missing.append("Action")
    if result < 5:
        missing.append("Result")

    if overall >= 7.5:
        verdict = "Strong STAR structure — clear context, action, and outcome."
    elif overall >= 5.5:
        verdict = "Partial STAR — add more detail on " + ", ".join(missing[:2]) + "."
    elif missing:
        verdict = "Use STAR: define " + ", ".join(missing) + " for stronger behavioural answers."
    else:
        verdict = "Expand your answer with specific situation, actions taken, and measurable results."

    return {
        "situation": situation,
        "task": task,
        "action": action,
        "result": result,
        "overall": overall,
        "verdict": verdict,
    }


def analyse_session_star(transcript: list) -> dict | None:
    """Aggregate STAR analysis across behavioural turns in a session."""
    texts: list[str] = []
    for turn in transcript or []:
        phase = turn.get("phase") or ""
        student = (turn.get("student_text") or "").strip()
        if student and (phase in _BEHAVIORAL_PHASES or "behav" in phase):
            texts.append(student)

    if not texts:
        # Fall back to longest student answers if no behavioural phase tagged.
        texts = [
            (t.get("student_text") or "").strip()
            for t in (transcript or [])
            if len((t.get("student_text") or "").strip()) >= 40
        ][:5]

    if not texts:
        return None

    combined = " ".join(texts)
    base = analyse_star_text(combined)
    per_answer = [analyse_star_text(t) for t in texts[:6]]
    return {
        **base,
        "answers_analysed": len(texts),
        "per_answer": per_answer,
    }


def delivery_score(
    posture: int | None,
    eye_contact: int | None,
    wpm: float | None,
    filler_pct: float | None,
) -> dict:
    """Composite delivery score (0–100) from body language + speech metrics."""
    posture_s = posture if posture is not None else 85
    eye_s = eye_contact if eye_contact is not None else 80

    if wpm is None or wpm <= 0:
        pace_s = 75
        pace_label = "Not enough speech for pace analysis"
    elif 90 <= wpm <= 155:
        pace_s = 95
        pace_label = "Ideal speaking pace"
    elif 155 < wpm <= 175:
        pace_s = 72
        pace_label = "Slightly fast — pause between points"
    elif wpm < 90:
        pace_s = 68
        pace_label = "Slow pace — add energy and clarity"
    else:
        pace_s = 60
        pace_label = "Too fast — slow down for clarity"

    filler = filler_pct if filler_pct is not None else 0.0
    filler_s = max(40, min(100, int(100 - filler * 4)))

    overall = round((posture_s * 0.25 + eye_s * 0.25 + pace_s * 0.25 + filler_s * 0.25))
    return {
        "overall": overall,
        "posture": posture_s,
        "eye_contact": eye_s,
        "pace": pace_s,
        "filler_control": filler_s,
        "pace_label": pace_label,
    }


def turn_heatmap(transcript: list, breakdown: list) -> list[dict]:
    """Per-question score strip for report heatmap (1–10)."""
    by_turn = {t.get("turn"): t for t in breakdown}
    items = []
    for turn in transcript or []:
        num = turn.get("turn")
        if num is None:
            continue
        fb = by_turn.get(num, {})
        score = fb.get("score")
        if score is None:
            continue
        items.append({
            "turn": num,
            "phase": turn.get("phase") or "",
            "score": max(0, min(10, int(score))),
            "label": f"Q{len(items) + 1}",
        })
    return items


def build_progress_insights(data: dict) -> dict:
    """Dynamic 'going well' / 'work on' bullets from aggregated session data."""
    going_well: list[str] = []
    work_on: list[str] = []

    score_timeline = data.get("score_timeline") or []
    scores = [s["score"] for s in score_timeline if s.get("score") is not None]
    by_skill = data.get("by_skill") or {}
    filler_timeline = data.get("filler_timeline") or []
    wpm_timeline = data.get("wpm_timeline") or []
    insights = data.get("insights") or {}

    if len(scores) >= 2 and scores[-1] > scores[-2]:
        delta = round(scores[-1] - scores[-2])
        going_well.append(
            f"Your overall score improved by {delta} points since your previous session."
        )

    if scores and scores[-1] >= 75:
        going_well.append(
            f"Latest session scored {round(scores[-1])}/100 — strong interview performance."
        )

    strongest = insights.get("strongest_skill")
    if strongest and by_skill.get(strongest, 0) >= 6.5:
        going_well.append(
            f"Strongest area: {_SKILL_LABELS.get(strongest, strongest.replace('_', ' ').title())} "
            f"(avg {by_skill[strongest]:.1f}/10)."
        )

    if insights.get("filler_improving"):
        going_well.append("Filler word usage is trending down across your sessions.")

    wpms = [w["value"] for w in wpm_timeline if w.get("value")]
    if wpms:
        avg_wpm = sum(wpms) / len(wpms)
        if 95 <= avg_wpm <= 150:
            going_well.append(
                f"Speaking pace is interview-ready (~{round(avg_wpm)} WPM) — clear and easy to follow."
            )

    weakest = insights.get("weakest_skill")
    if weakest and by_skill.get(weakest, 10) < 7:
        work_on.append(
            f"Focus on {_SKILL_LABELS.get(weakest, weakest.replace('_', ' ').title())} "
            f"— averaging {by_skill[weakest]:.1f}/10 across sessions."
        )

    fillers = [f["value"] for f in filler_timeline if f.get("value") is not None]
    if fillers and fillers[-1] >= 8:
        work_on.append(
            f"Reduce filler words — {fillers[-1]} detected in your latest session. "
            "Pause silently instead of saying 'um' or 'basically'."
        )

    if wpms and wpms[-1] > 165:
        work_on.append(
            "Slow down slightly — your latest pace was fast. Aim for 110–140 words per minute."
        )
    elif wpms and wpms[-1] < 85 and wpms[-1] > 0:
        work_on.append(
            "Add more energy to your delivery — your speaking pace was slower than ideal."
        )

    work_on.append(
        "Use the STAR method (Situation, Task, Action, Result) for behavioural questions."
    )

    if not going_well:
        going_well.append(
            "You're building interview momentum — each session adds data to your progress charts."
        )

    # De-dupe work_on STAR tip if already weak on behavioral
    if weakest == "behavioral":
        work_on = [w for w in work_on if "STAR method" not in w]

    return {
        "going_well": going_well[:4],
        "work_on": work_on[:4],
    }

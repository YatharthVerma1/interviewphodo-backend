"""Speech analysis — filler detection, WPM, pace verdicts."""

from __future__ import annotations

import re

# Single-word and multi-word fillers common in Indian English interviews.
FILLER_WORDS = [
    "um", "uh", "uhh", "umm", "hmm", "hm",
    "like", "basically", "actually", "literally",
    "you know", "sort of", "kind of", "i mean",
    "right", "okay so", "means", "matlab", "na", "ya know",
]

FILLER_FEEDBACK_HINTS = (
    "filler",
    "fillers",
    "filler word",
    "avoid saying",
    "instead of saying",
    "watch out",
    "you used",
    "you said",
    "you're using",
    "you are using",
    "cut down",
    "too many",
    "reduce",
    "pause instead",
    "try not to say",
)

# Pre-compile patterns once at import time.
_FILLER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"\b{re.escape(fw)}\b", re.IGNORECASE), fw)
    for fw in sorted(FILLER_WORDS, key=len, reverse=True)
]


def detect_filler_words(text: str) -> list[str]:
    """Detect filler words in student speech text (word-boundary aware)."""
    if not text:
        return []
    found: list[str] = []
    for pattern, name in _FILLER_PATTERNS:
        found.extend([name] * len(pattern.findall(text)))
    return found


def infer_fillers_from_ai_feedback(ai_text: str) -> list[str]:
    """Infer fillers from AI feedback when STT drops disfluencies from transcripts.

    Gemini Live hears audio directly and often comments on fillers even when
    the text transcription omits 'um', 'basically', etc.
    """
    if not ai_text:
        return []
    lower = ai_text.lower()
    if not any(h in lower for h in FILLER_FEEDBACK_HINTS):
        return []
    found: list[str] = []
    for pattern, name in _FILLER_PATTERNS:
        matches = pattern.findall(lower)
        if matches:
            found.extend([name] * len(matches))
    return found


def detect_fillers_combined(student_text: str, ai_text: str = "") -> list[str]:
    """Best-effort filler list from student STT + AI spoken feedback."""
    from_stt = detect_filler_words(student_text)
    from_ai = infer_fillers_from_ai_feedback(ai_text)
    if not from_ai:
        return from_stt
    if not from_stt:
        return from_ai
    # Merge — AI may catch fillers STT missed.
    seen = set(from_stt)
    merged = list(from_stt)
    for fw in from_ai:
        if fw not in seen:
            merged.append(fw)
            seen.add(fw)
        elif from_ai.count(fw) > from_stt.count(fw):
            merged.append(fw)
    return merged


def count_fillers_in_transcript(transcript: list) -> int:
    """Total filler count across all turns, using stored + inferred data."""
    total = 0
    for turn in transcript or []:
        stored = turn.get("filler_words") or []
        if stored:
            total += len(stored)
            continue
        total += len(detect_fillers_combined(
            turn.get("student_text") or "",
            turn.get("ai_text") or "",
        ))
    return total


def analyse_full_transcript(transcript: list, duration_seconds: float) -> dict:
    """Full post-session speech analysis."""
    if not transcript or duration_seconds <= 0:
        return {}

    all_student_text = " ".join(t.get("student_text", "") for t in transcript)
    words = all_student_text.lower().split()
    total_words = len(words)
    filler_count = count_fillers_in_transcript(transcript)
    wpm = (total_words / duration_seconds) * 60 if duration_seconds > 0 else 0

    if total_words == 0:
        pace_verdict = "Not enough speech captured for pace analysis"
    elif wpm > 160:
        pace_verdict = "Too fast — slow down"
    elif wpm < 90:
        pace_verdict = "Too slow — speak with more energy"
    else:
        pace_verdict = "Good pace"

    return {
        "total_words":  total_words,
        "filler_count": filler_count,
        "filler_pct":   round((filler_count / max(total_words, 1)) * 100, 1),
        "words_per_min": round(wpm, 1),
        "pace_verdict": pace_verdict,
        "filler_verdict": (
            "Excellent — very few filler words" if filler_count <= 3
            else f"Reduce filler words — used {filler_count} times. "
                 "Practice pausing silently instead of saying 'um' or 'basically'."
        ),
    }


def total_filler_count_for_state(state) -> int:
    """Pick the highest reliable filler total for report generation."""
    transcript = getattr(state, "transcript", []) or []
    speech = analyse_full_transcript(
        transcript,
        getattr(state, "get_interview_elapsed_seconds", lambda: 1)() or 1,
    )
    return max(
        speech.get("filler_count", 0),
        getattr(state, "filler_count", 0) or 0,
        count_fillers_in_transcript(transcript),
    )

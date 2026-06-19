FILLER_WORDS = [
    "um", "uh", "like", "basically", "actually", "you know",
    "sort of", "kind of", "right", "okay so", "means", "matlab",
]


def detect_filler_words(text: str) -> list[str]:
    """Detect filler words in a single student utterance."""
    if not text:
        return []
    lower = text.lower()
    found = []
    for fw in FILLER_WORDS:
        count = lower.split().count(fw) if " " not in fw else lower.count(fw)
        found.extend([fw] * count)
    return found


def analyse_full_transcript(transcript: list, duration_seconds: float) -> dict:
    """
    Full post-session speech analysis.
    Called by report_generator after the interview ends.
    """
    if not transcript or duration_seconds <= 0:
        return {}

    all_student_text = " ".join(t.get("student_text", "") for t in transcript)
    words = all_student_text.lower().split()
    total_words = len(words)
    filler_count = sum(len(detect_filler_words(t.get("student_text", ""))) for t in transcript)
    wpm = (total_words / duration_seconds) * 60 if duration_seconds > 0 else 0

    return {
        "total_words":  total_words,
        "filler_count": filler_count,
        "filler_pct":   round((filler_count / max(total_words, 1)) * 100, 1),
        "words_per_min": round(wpm, 1),
        "pace_verdict": (
            "Too fast — slow down" if wpm > 160
            else "Too slow — speak with more energy" if wpm < 90
            else "Good pace"
        ),
        "filler_verdict": (
            "Excellent — very few filler words" if filler_count <= 3
            else f"Reduce filler words — used {filler_count} times. "
                 "Practice pausing silently instead of saying 'um' or 'basically'."
        ),
    }

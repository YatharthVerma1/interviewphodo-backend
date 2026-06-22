"""
Interview FSM — interviewphodo.com
====================================
Controls the strict structural flow of every interview session.
Gemini is never told to manage the interview flow itself.
The backend decides when to advance phases and rebuilds the prompt accordingly.

Interview rounds covered (matching Indian company placement process):
- INTRO         → warm-up, tell me about yourself
- RESUME        → questions from the student's actual resume
- TECHNICAL     → verbal explanation of DSA, OOP, DBMS, OS (NOT live coding)
- BEHAVIORAL    → STAR-format situational questions
- HR_ROUND      → India-specific questions: bond, relocation, CTC, why company
- CANDIDATE_QA  → student asks questions
- CLOSING       → structured verbal performance report

NOT in V1: Round 1 (Online coding test — solo, not interactive)
            Round 4 (System Design — for experienced only)

ROUND TYPES — mapped to actual Indian placement rounds the user picks:
  technical  → Round 2-3 (Technical: DSA + Core CS + Project deep-dive)
  managerial → Round 5 (Managerial: situational, leadership, project ownership, fitment)
  hr         → Round 6 (HR: salary, career, background verification, India trap questions)
  full       → All-in-one practice (every phase, longer)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)


class InterviewPhase(Enum):
    INTRO        = "intro"
    RESUME       = "resume_review"
    TECHNICAL    = "technical_qa"
    BEHAVIORAL   = "behavioral"
    HR_ROUND     = "hr_round"
    CANDIDATE_QA = "candidate_qa"
    CLOSING      = "closing"


# Hero phase per round — used when extending interviews that finish too quickly.
HERO_PHASE_BY_ROUND: dict[str, InterviewPhase] = {
    "technical":     InterviewPhase.TECHNICAL,
    "managerial":    InterviewPhase.BEHAVIORAL,
    "hr":            InterviewPhase.HR_ROUND,
    "full":          InterviewPhase.TECHNICAL,
    "coaching":      InterviewPhase.BEHAVIORAL,
    "multi_persona": InterviewPhase.TECHNICAL,
    "mixed":         InterviewPhase.TECHNICAL,
}

# Per-round phase plan: (phase, turns_in_phase).
# Turn budgets target ~25–30 min at ~25–40 sec/turn. Doubled from V1 so fast
# answers do not exhaust content before the 25-min wall-clock minimum.
ROUND_PHASE_PLAN: dict[str, list[tuple["InterviewPhase", int]]] = {
    "technical": [
        (InterviewPhase.INTRO,        3),
        (InterviewPhase.RESUME,      12),
        (InterviewPhase.TECHNICAL,   32),
        (InterviewPhase.BEHAVIORAL,  26),
        (InterviewPhase.CANDIDATE_QA, 12),
        (InterviewPhase.CLOSING,      4),
    ],
    "managerial": [
        (InterviewPhase.INTRO,        3),
        (InterviewPhase.RESUME,      14),
        (InterviewPhase.BEHAVIORAL,  32),
        (InterviewPhase.CANDIDATE_QA, 14),
        (InterviewPhase.CLOSING,      4),
    ],
    "hr": [
        (InterviewPhase.INTRO,        3),
        (InterviewPhase.RESUME,      12),
        (InterviewPhase.HR_ROUND,    32),
        (InterviewPhase.BEHAVIORAL,  26),
        (InterviewPhase.CANDIDATE_QA, 12),
        (InterviewPhase.CLOSING,      4),
    ],
    "full": [
        (InterviewPhase.INTRO,        3),
        (InterviewPhase.RESUME,      12),
        (InterviewPhase.TECHNICAL,   20),
        (InterviewPhase.BEHAVIORAL,  34),
        (InterviewPhase.HR_ROUND,    34),
        (InterviewPhase.CANDIDATE_QA, 16),
        (InterviewPhase.CLOSING,      4),
    ],
    "coaching": [
        (InterviewPhase.INTRO,        3),
        (InterviewPhase.RESUME,      10),
        (InterviewPhase.TECHNICAL,   12),
        # Coaching uses ~2 student turns per coached question — budgets are high
        # so behavioral / HR / Q&A still feel as long as intro + resume + technical.
        (InterviewPhase.BEHAVIORAL,  30),
        (InterviewPhase.HR_ROUND,    30),
        (InterviewPhase.CANDIDATE_QA, 14),
        (InterviewPhase.CLOSING,      4),
    ],
    "multi_persona": [
        (InterviewPhase.INTRO,        3),
        (InterviewPhase.RESUME,      14),
        (InterviewPhase.TECHNICAL,   22),
        (InterviewPhase.BEHAVIORAL,  30),
        (InterviewPhase.HR_ROUND,    30),
        (InterviewPhase.CANDIDATE_QA, 14),
        (InterviewPhase.CLOSING,      4),
    ],
}

# Backward-compat: old code/users that pass "mixed" → "full"
ROUND_PHASE_PLAN["mixed"] = ROUND_PHASE_PLAN["full"]

# Default full phase order (legacy fallback)
FULL_PHASE_ORDER = [phase for phase, _ in ROUND_PHASE_PLAN["full"]]


@dataclass
class InterviewState:
    session_id:    str
    user_id:       str
    company:       str        # tcs | infosys | wipro | hcl | accenture | cognizant | tech_mahindra | zoho
    round_type:    str        # technical | managerial | hr | full
    resume_text:   str = ""

    current_phase: InterviewPhase = InterviewPhase.INTRO
    phase_turn:    int = 0         # turns completed in current phase
    total_turns:   int = 0
    filler_count:  int = 0

    transcript:    list = field(default_factory=list)
    phase_scores:  dict = field(default_factory=dict)
    posture_events: list = field(default_factory=list)
    phase_order:   list = field(default_factory=list)
    phase_budgets: dict = field(default_factory=dict)
    # Topics already asked to this user across past sessions (cross-session
    # memory). Populated at session start so the prompt can tell Gemini
    # "do not repeat any of these questions".
    past_topics:   list = field(default_factory=list)
    target_role:   Optional[str] = None
    # Persona for the CURRENT speaker. In normal rounds this is set once at
    # session start. In `multi_persona` rounds it gets swapped on phase change.
    interviewer:   dict = field(default_factory=dict)
    # Multi-persona rounds only: phase_value -> persona dict. When set, the
    # turn processor swaps `interviewer` to the right persona at every phase
    # boundary and announces a handoff to the candidate.
    personas_by_phase: dict = field(default_factory=dict)
    # Difficulty level inferred from how many sessions this user has done
    # for THIS company before: 'easy' (first try), 'medium', or 'hard'.
    # Can be overridden by user-supplied value at session start.
    difficulty_level: str = "medium"
    dynamic_injection_count: int = 0
    # Tracks mid-phase Gemini injections at 50% / 75% of each phase budget.
    mid_injection_marks: set = field(default_factory=set)
    started_at:    float = field(default_factory=time.time)
    # Set when the student actually joins the Daily room (interview clock starts).
    joined_at:     Optional[float] = None

    def __post_init__(self):
        plan = ROUND_PHASE_PLAN.get(
            self.round_type, ROUND_PHASE_PLAN["full"]
        )
        self.phase_order   = [p for p, _ in plan]
        self.phase_budgets = {p: n for p, n in plan}

    def advance_phase(self) -> bool:
        try:
            idx = self.phase_order.index(self.current_phase)
        except ValueError:
            return False
        if idx < len(self.phase_order) - 1:
            next_phase = self.phase_order[idx + 1]
            if next_phase == InterviewPhase.CLOSING and self.should_block_closing():
                logger.info(
                    f"Blocking early CLOSING | session={self.session_id} "
                    f"elapsed={self.get_interview_elapsed_seconds()}s"
                )
                return False
            self.current_phase = next_phase
            self.phase_turn = 0
            return True
        return False

    def should_block_closing(self) -> bool:
        """Do not enter CLOSING until ~23 min — prevents early report + silence."""
        from services.interview_timing import MIN_INTERVIEW_SEC
        return self.get_interview_elapsed_seconds() < (MIN_INTERVIEW_SEC - 120)

    def jump_to_phase(self, phase: "InterviewPhase") -> bool:
        """Skip ahead to a specific phase (used by the time watchdog to
        force CLOSING when wall-clock budget is almost exhausted)."""
        if phase not in self.phase_order:
            return False
        self.current_phase = phase
        self.phase_turn = 0
        return True

    def get_phase_budget(self, phase: Optional[InterviewPhase] = None) -> int:
        return self.phase_budgets.get(phase or self.current_phase, 4)

    def persona_for_phase(self, phase: Optional["InterviewPhase"] = None) -> dict:
        """Return the persona who should be speaking for `phase`. In normal
        rounds this is always `self.interviewer`. In multi_persona rounds it
        looks up `personas_by_phase`."""
        target = phase or self.current_phase
        if self.personas_by_phase:
            return self.personas_by_phase.get(target.value, self.interviewer) or self.interviewer
        return self.interviewer

    def should_advance(self) -> bool:
        return self.phase_turn >= self.get_phase_budget()

    def is_fsm_finished(self) -> bool:
        """True when all planned phases/turns are exhausted (ignores wall clock)."""
        return (
            self.current_phase == InterviewPhase.CLOSING
            and self.phase_turn >= self.get_phase_budget(InterviewPhase.CLOSING)
        )

    def is_complete(self) -> bool:
        """Interview may end naturally only after FSM is done AND 25+ min elapsed."""
        from services.interview_timing import MIN_INTERVIEW_SEC
        if not self.is_fsm_finished():
            return False
        return self.get_interview_elapsed_seconds() >= MIN_INTERVIEW_SEC

    def hero_phase(self) -> InterviewPhase:
        return HERO_PHASE_BY_ROUND.get(self.round_type, InterviewPhase.BEHAVIORAL)

    def get_interview_elapsed_seconds(self) -> int:
        """Wall-clock seconds since the student joined (falls back to session age)."""
        if self.joined_at is not None:
            return int(time.time() - self.joined_at)
        return self.get_duration_seconds()

    def extend_if_under_minimum(self, min_sec: int, extra_turns: int = 10) -> bool:
        """Keep the interview going until the 25-min wall-clock minimum is met.

        When the FSM runs out of turns too quickly (common with fast answers),
        jump back to the round's hero phase for deeper follow-up questions
        instead of ending after only a few minutes.
        """
        if self.get_interview_elapsed_seconds() >= min_sec:
            return False

        hero = self.hero_phase()

        if self.is_fsm_finished() or self.current_phase == InterviewPhase.CLOSING:
            # Rewind to hero phase — e.g. more HR traps, more technical depth.
            self.current_phase = hero
            self.phase_turn = 0
            self.phase_budgets[hero] = self.phase_budgets.get(hero, 6) + extra_turns
            logger_msg = f"extended hero phase {hero.value} +{extra_turns} turns"
        else:
            self.phase_budgets[self.current_phase] = self.phase_turn + extra_turns
            logger_msg = f"extended {self.current_phase.value} +{extra_turns} turns"

        logger.info(
            f"Interview extension | session={self.session_id} "
            f"elapsed={self.get_interview_elapsed_seconds()}s | {logger_msg}"
        )
        return True

    def extend_current_phase(self, extra_turns: int = 4) -> None:
        """Add turns to the active phase when CLOSING is blocked or pacing is ahead."""
        self.phase_budgets[self.current_phase] = self.phase_turn + extra_turns
        logger.info(
            f"Phase extended | session={self.session_id} "
            f"phase={self.current_phase.value} +{extra_turns} turns"
        )

    def total_turn_budget(self) -> int:
        return sum(self.phase_budgets.values())

    def pacing_ahead_of_schedule(self) -> bool:
        """True when turn consumption is faster than the 25-min target pace."""
        from services.interview_timing import MIN_INTERVIEW_SEC
        elapsed = self.get_interview_elapsed_seconds()
        if elapsed >= MIN_INTERVIEW_SEC or self.total_turns < 3:
            return False
        progress = elapsed / MIN_INTERVIEW_SEC
        expected_turns = int(self.total_turn_budget() * progress * 0.75)
        return self.total_turns >= max(expected_turns + 4, 8)

    def extend_later_phases_if_early(self, min_elapsed_sec: int = 20 * 60) -> bool:
        """Top up remaining phase budgets when the session is still short on time."""
        from services.interview_timing import MIN_INTERVIEW_SEC

        elapsed = self.get_interview_elapsed_seconds()
        if elapsed >= min_elapsed_sec or elapsed >= MIN_INTERVIEW_SEC:
            return False

        floors = {
            InterviewPhase.TECHNICAL: 28,
            InterviewPhase.BEHAVIORAL: 26,
            InterviewPhase.HR_ROUND: 26,
            InterviewPhase.CANDIDATE_QA: 12,
            InterviewPhase.RESUME: 12,
        }
        if self.round_type == "coaching":
            floors = {k: v + 4 for k, v in floors.items()}

        boosted = False
        current_idx = self.phase_order.index(self.current_phase) if self.current_phase in self.phase_order else -1
        for phase in self.phase_order[current_idx + 1:]:
            if phase == InterviewPhase.CLOSING:
                continue
            floor = floors.get(phase, 18)
            if self.phase_budgets.get(phase, 0) < floor:
                self.phase_budgets[phase] = floor
                boosted = True
        return boosted

    def mid_inject_milestone(self) -> Optional[int]:
        """Return 75 if a mid-phase question-bank refresh should run now."""
        if self.current_phase in {
            InterviewPhase.INTRO,
            InterviewPhase.CLOSING,
        }:
            return None
        budget = self.get_phase_budget()
        if budget < 6:
            return None
        pct = 75
        mark = f"{self.current_phase.value}:{pct}"
        if mark in self.mid_injection_marks:
            return None
        threshold = max(1, (budget * pct) // 100)
        if self.phase_turn >= threshold:
            return pct
        return None

    def mark_mid_injected(self, pct: int) -> None:
        self.mid_injection_marks.add(f"{self.current_phase.value}:{pct}")

    def record_turn(
        self,
        student_text: str,
        ai_text: str,
        score: Optional[int] = None,
        feedback: Optional[str] = None,
        filler_words: Optional[list] = None,
        counts_toward_phase: bool = True,
    ):
        self.transcript.append({
            "turn": self.total_turns + 1,
            "phase": self.current_phase.value,
            "student_text": student_text,
            "ai_text": ai_text,
            "score": score,
            "feedback": feedback or "",
            "filler_words": filler_words or [],
            "substantive": counts_toward_phase,
            "timestamp": time.time(),
        })
        if score is not None and counts_toward_phase:
            self.phase_scores.setdefault(self.current_phase.value, []).append(score)
        if filler_words:
            self.filler_count += len(filler_words)
        if counts_toward_phase:
            self.phase_turn += 1
        self.total_turns += 1

    def add_posture_event(self, event_type: str, message: str):
        self.posture_events.append({
            "type": event_type,
            "message": message,
            "phase": self.current_phase.value,
            "turn": self.total_turns,
            "timestamp": time.time(),
        })

    def get_duration_seconds(self) -> int:
        return int(time.time() - self.started_at)

    def get_overall_score(self) -> int:
        all_scores = [s for scores in self.phase_scores.values() for s in scores]
        if not all_scores:
            return 0
        return min(100, round((sum(all_scores) / len(all_scores)) * 10))

    def rebalance_budget(self, target_total_sec: float | None = None) -> bool:
        """If we're running long, shrink remaining phase budgets so the
        interview still finishes within the target wall-clock window.

        Triggers proportional shrinking when the average seconds-per-turn
        observed so far would push total time past the target. CLOSING is
        protected (always keeps its full budget so the report still gets
        delivered properly).

        Returns True if budgets were rebalanced this turn, False otherwise.
        """
        from services.interview_timing import MIN_INTERVIEW_SEC, REBALANCE_TARGET_SEC

        if target_total_sec is None:
            target_total_sec = REBALANCE_TARGET_SEC

        elapsed = self.get_interview_elapsed_seconds()
        # Never shrink phases while we are still under the 25-min minimum.
        if elapsed < MIN_INTERVIEW_SEC:
            return False
        if self.total_turns < 4 or elapsed <= 0:
            return False  # need a few real turns of data first

        avg_sec_per_turn = elapsed / self.total_turns
        remaining_sec = target_total_sec - elapsed
        if remaining_sec <= 0:
            return False

        try:
            current_idx = self.phase_order.index(self.current_phase)
        except ValueError:
            return False

        current_remaining = max(0, self.get_phase_budget(self.current_phase) - self.phase_turn)
        upcoming_phases   = self.phase_order[current_idx + 1:]
        upcoming_planned  = sum(self.phase_budgets.get(p, 0) for p in upcoming_phases)
        total_planned     = current_remaining + upcoming_planned
        if total_planned <= 0:
            return False

        affordable = int(remaining_sec / max(avg_sec_per_turn, 30))
        if affordable >= total_planned:
            return False  # we're on time, nothing to do

        ratio = affordable / total_planned
        # Shrink current phase's *remaining* turns
        new_current = max(1, int(round(current_remaining * ratio)))
        self.phase_budgets[self.current_phase] = self.phase_turn + new_current
        # Shrink upcoming phases (CLOSING is protected — students need their report)
        for p in upcoming_phases:
            if p == InterviewPhase.CLOSING:
                continue
            old = self.phase_budgets.get(p, 1)
            self.phase_budgets[p] = max(1, int(round(old * ratio)))
        return True

    def to_db_dict(self) -> dict:
        return {
            "current_phase": self.current_phase.value,
            "phase_turn": self.phase_turn,
            "total_turns": self.total_turns,
            "filler_count": self.filler_count,
            "transcript": self.transcript,
            "posture_events": self.posture_events,
        }


# In-memory session store: session_id → InterviewState
# Works for V1 single Railway instance. Replace with Redis in V2.
active_sessions: dict[str, InterviewState] = {}


def create_session_state(
    session_id: str,
    user_id: str,
    company: str,
    round_type: str,
    resume_text: str = "",
    past_topics: Optional[list] = None,
    interviewer: Optional[dict] = None,
    personas_by_phase: Optional[dict] = None,
    difficulty_level: str = "medium",
    target_role: Optional[str] = None,
) -> InterviewState:
    state = InterviewState(
        session_id=session_id,
        user_id=user_id,
        company=company,
        round_type=round_type,
        resume_text=resume_text,
        past_topics=past_topics or [],
        interviewer=interviewer or {},
        personas_by_phase=personas_by_phase or {},
        difficulty_level=difficulty_level,
        target_role=target_role,
    )
    active_sessions[session_id] = state
    return state


def get_session_state(session_id: str) -> Optional[InterviewState]:
    return active_sessions.get(session_id)


def remove_session_state(session_id: str):
    active_sessions.pop(session_id, None)

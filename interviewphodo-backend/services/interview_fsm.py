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
- BEHAVIORAL    → STAR-format situational questions (Round 5 equivalent)
- HR_ROUND      → India-specific questions: bond, relocation, CTC, why company
- CANDIDATE_QA  → student asks questions
- CLOSING       → structured verbal performance report

NOT in V1: Online coding test (Round 1), System Design (Round 4 — for experienced only)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time


class InterviewPhase(Enum):
    INTRO        = "intro"
    RESUME       = "resume_review"
    TECHNICAL    = "technical_qa"
    BEHAVIORAL   = "behavioral"
    HR_ROUND     = "hr_round"
    CANDIDATE_QA = "candidate_qa"
    CLOSING      = "closing"


# Turn budget per phase — one turn = student speaks + AI responds
PHASE_BUDGETS = {
    InterviewPhase.INTRO:        2,
    InterviewPhase.RESUME:       3,
    InterviewPhase.TECHNICAL:    4,
    InterviewPhase.BEHAVIORAL:   3,
    InterviewPhase.HR_ROUND:     3,
    InterviewPhase.CANDIDATE_QA: 2,
    InterviewPhase.CLOSING:      1,
}

# Default full phase order
FULL_PHASE_ORDER = [
    InterviewPhase.INTRO,
    InterviewPhase.RESUME,
    InterviewPhase.TECHNICAL,
    InterviewPhase.BEHAVIORAL,
    InterviewPhase.HR_ROUND,
    InterviewPhase.CANDIDATE_QA,
    InterviewPhase.CLOSING,
]

# Phase order per round type
ROUND_PHASES = {
    "hr": [
        InterviewPhase.INTRO,
        InterviewPhase.RESUME,
        InterviewPhase.BEHAVIORAL,
        InterviewPhase.HR_ROUND,
        InterviewPhase.CANDIDATE_QA,
        InterviewPhase.CLOSING,
    ],
    "technical": [
        InterviewPhase.INTRO,
        InterviewPhase.RESUME,
        InterviewPhase.TECHNICAL,
        InterviewPhase.BEHAVIORAL,
        InterviewPhase.CANDIDATE_QA,
        InterviewPhase.CLOSING,
    ],
    "mixed": FULL_PHASE_ORDER,
}


@dataclass
class InterviewState:
    session_id:    str
    user_id:       str
    company:       str        # tcs | infosys | wipro | hcl | accenture | cognizant | tech_mahindra | zoho
    round_type:    str        # hr | technical | mixed
    resume_text:   str = ""

    current_phase: InterviewPhase = InterviewPhase.INTRO
    phase_turn:    int = 0         # turns completed in current phase
    total_turns:   int = 0
    filler_count:  int = 0

    transcript:    list = field(default_factory=list)
    phase_scores:  dict = field(default_factory=dict)
    posture_events: list = field(default_factory=list)
    phase_order:   list = field(default_factory=list)
    started_at:    float = field(default_factory=time.time)

    def __post_init__(self):
        self.phase_order = ROUND_PHASES.get(self.round_type, FULL_PHASE_ORDER)

    def advance_phase(self) -> bool:
        try:
            idx = self.phase_order.index(self.current_phase)
        except ValueError:
            return False
        if idx < len(self.phase_order) - 1:
            self.current_phase = self.phase_order[idx + 1]
            self.phase_turn = 0
            return True
        return False

    def should_advance(self) -> bool:
        return self.phase_turn >= PHASE_BUDGETS.get(self.current_phase, 999)

    def is_complete(self) -> bool:
        return (
            self.current_phase == InterviewPhase.CLOSING
            and self.phase_turn >= PHASE_BUDGETS[InterviewPhase.CLOSING]
        )

    def record_turn(
        self,
        student_text: str,
        ai_text: str,
        score: Optional[int] = None,
        filler_words: Optional[list] = None,
    ):
        self.transcript.append({
            "turn": self.total_turns + 1,
            "phase": self.current_phase.value,
            "student_text": student_text,
            "ai_text": ai_text,
            "score": score,
            "filler_words": filler_words or [],
            "timestamp": time.time(),
        })
        if score is not None:
            self.phase_scores.setdefault(self.current_phase.value, []).append(score)
        if filler_words:
            self.filler_count += len(filler_words)
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
) -> InterviewState:
    state = InterviewState(
        session_id=session_id,
        user_id=user_id,
        company=company,
        round_type=round_type,
        resume_text=resume_text,
    )
    active_sessions[session_id] = state
    return state


def get_session_state(session_id: str) -> Optional[InterviewState]:
    return active_sessions.get(session_id)


def remove_session_state(session_id: str):
    active_sessions.pop(session_id, None)

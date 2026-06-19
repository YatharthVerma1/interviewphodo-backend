"""
Pipecat real-time interview pipeline — interviewphodo.com
Compatible with pipecat-ai 0.0.108 (Python 3.11 or 3.12).
Pipecat is imported inside run_interview_pipeline() so the API can start
without Pipecat when using the base requirements.txt only.
"""

import asyncio
import time

from loguru import logger

from config import settings
from database.supabase_client import supabase_admin

# ---------------------------------------------------------------------------
# Daily global-context guard.
#
# daily-python's native context (Daily.init/Daily.deinit) is a PROCESS-WIDE
# singleton. Calling Daily.deinit() while ANOTHER session is still using the
# context crashes the whole process with a non-unwinding Rust panic
# (exit 134). That happens whenever two interviews end close together.
#
# We reference-count live pipelines and only deinit when the LAST one ends.
# The lock serialises the increment/decrement + deinit decision.
# ---------------------------------------------------------------------------
_active_pipeline_count = 0
_daily_lock = asyncio.Lock()


async def _register_pipeline_start():
    global _active_pipeline_count
    async with _daily_lock:
        _active_pipeline_count += 1
        logger.debug(f"Active pipelines: {_active_pipeline_count}")


async def _register_pipeline_end():
    """Decrement the live-pipeline count; deinit Daily only when it hits 0."""
    global _active_pipeline_count
    async with _daily_lock:
        _active_pipeline_count = max(0, _active_pipeline_count - 1)
        logger.debug(f"Active pipelines: {_active_pipeline_count}")
        if _active_pipeline_count == 0:
            try:
                from daily import Daily
                Daily.deinit()
                logger.debug("Daily.deinit() — no active pipelines remain")
            except Exception as cleanup_err:
                logger.debug(f"Daily.deinit cleanup skipped: {cleanup_err}")
from prompts.companies import (
    build_personas_by_phase,
    pick_interviewer,
    pick_multi_personas,
)
from prompts.fsm_prompt_builder import build_system_prompt
from services.avatar_broadcaster import broadcast, remove_session_connections
from services.interview_fsm import (
    InterviewPhase,
    InterviewState,
    create_session_state,
    remove_session_state,
)
from services.interview_timing import (
    FORCE_CLOSE_AT,
    GOODBYE_AT,
    MAX_INTERVIEW_SEC,
    MIN_INTERVIEW_SEC,
    REBALANCE_TARGET_SEC,
    WARN_5MIN_AT,
)
from services.speech_analyser import detect_filler_words
from services.turn_scorer import score_turn


def _fetch_past_company_history(
    user_id: str, company: str, limit_sessions: int = 4
) -> tuple[list[str], int]:
    """Pull this user's past sessions for the same company.

    Returns:
        past_topics      - AI questions already asked (for the 'do not repeat' rule).
        completed_count  - how many completed sessions for this company → drives difficulty.
    """
    try:
        rows = supabase_admin.table("sessions").select(
            "transcript, status"
        ).eq("user_id", user_id).eq("company", company).order(
            "created_at", desc=True
        ).limit(limit_sessions).execute()
    except Exception as e:
        logger.error(f"Failed to fetch past sessions: {e}")
        return [], 0

    topics: list[str] = []
    completed_count = 0
    for row in rows.data or []:
        if row.get("status") == "completed":
            completed_count += 1
        for turn in (row.get("transcript") or []):
            ai_q = (turn.get("ai_text") or "").strip()
            if 25 <= len(ai_q) <= 220 and "?" in ai_q:
                topics.append(ai_q)

    # Dedupe preserving order; cap recent
    seen = set()
    deduped: list[str] = []
    for t in topics:
        key = t.lower()[:80]
        if key not in seen:
            seen.add(key)
            deduped.append(t)
    return deduped[:25], completed_count


def _difficulty_from_count(completed_count: int) -> str:
    """0 prior → easy (warm-up), 1-2 → medium, 3+ → hard."""
    if completed_count <= 0:
        return "easy"
    if completed_count <= 2:
        return "medium"
    return "hard"


async def _sync_state_to_db(state: InterviewState):
    try:
        supabase_admin.table("sessions").update(
            state.to_db_dict()
        ).eq("id", state.session_id).execute()
    except Exception as e:
        logger.error(f"DB sync error: {e}")


async def _end_interview(state: InterviewState, reason: str = "completed"):
    from services.report_generator import generate_report

    try:
        supabase_admin.table("sessions").update({
            **state.to_db_dict(),
            "status": "completed" if reason == "completed" else "abandoned",
            "ended_at": "now()",
            "duration_seconds": state.get_duration_seconds(),
        }).eq("id", state.session_id).execute()

        if reason == "completed" and state.total_turns >= 4:
            await generate_report(state)
    except Exception as e:
        logger.error(f"End interview error: {e}")


def _phase_to_expression(phase: str) -> str:
    return {
        "intro": "warm",
        "resume_review": "attentive",
        "technical_qa": "serious",
        "behavioral": "curious",
        "hr_round": "formal",
        "candidate_qa": "open",
        "closing": "reflective",
    }.get(phase, "neutral")


async def run_interview_pipeline(
    room_url: str,
    room_token: str,
    session_id: str,
    user_id: str,
    company: str,
    round_type: str,
    resume_text: str = "",
    difficulty_override: str | None = None,
):
    """Main pipeline runner — called as background task from /api/sessions/start."""
    try:
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.audio.vad.vad_analyzer import VADParams
        from pipecat.frames.frames import (
            EndFrame,
            LLMFullResponseEndFrame,
            LLMRunFrame,
            TextFrame,
            TranscriptionFrame,
        )
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.runner import PipelineRunner
        from pipecat.pipeline.task import PipelineParams, PipelineTask
        from pipecat.processors.aggregators.llm_context import LLMContext
        from pipecat.processors.aggregators.llm_response_universal import (
            LLMContextAggregatorPair,
        )
        from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
        from pipecat.services.google.gemini_live.llm import (
            GeminiLiveLLMService,
            GeminiModalities,
        )
        from pipecat.transports.services.daily import DailyParams, DailyTransport
    except ImportError as e:
        logger.error(
            "Pipecat not installed. Use Python 3.12 venv: "
            "pip install -r requirements-pipecat.txt"
        )
        try:
            supabase_admin.table("sessions").update({
                "status": "abandoned",
                "ended_at": "now()",
            }).eq("id", session_id).execute()
        except Exception:
            pass
        remove_session_state(session_id)
        raise RuntimeError(
            "Pipecat not available. Activate .venv312 and install requirements-pipecat.txt"
        ) from e

    class InterviewTurnProcessor(FrameProcessor):
        def __init__(self, state, session_id, gemini, **kwargs):
            super().__init__(**kwargs)
            self.state = state
            self.session_id = session_id
            self.gemini = gemini
            self.task = None
            self._last_user_text = ""
            self._ai_text_parts: list[str] = []

        async def _on_turn_complete(self):
            ai_text = " ".join(self._ai_text_parts).strip()
            self._ai_text_parts = []
            student_text = self._last_user_text.strip()
            self._last_user_text = ""

            fillers = detect_filler_words(student_text)
            turn_score, turn_feedback = score_turn(
                phase=self.state.current_phase.value,
                student_text=student_text,
                ai_text=ai_text,
                filler_words=fillers,
            )
            self.state.record_turn(
                student_text=student_text,
                ai_text=ai_text,
                score=turn_score,
                feedback=turn_feedback,
                filler_words=fillers,
            )

            if turn_score is not None:
                await broadcast(self.session_id, {
                    "type":     "turn_feedback",
                    "turn":     self.state.total_turns,
                    "phase":    self.state.current_phase.value,
                    "score":    turn_score,
                    "feedback": turn_feedback,
                })

            # Time-budget pre-check: if the student is taking long per answer,
            # shrink remaining phase budgets so we still finish on time.
            # Targets ~27 min of conversation, leaving buffer before the 30-min cap.
            if self.state.rebalance_budget(target_total_sec=REBALANCE_TARGET_SEC):
                logger.info(
                    f"Time-budget rebalanced | session={self.session_id} "
                    f"avg_per_turn={self.state.get_duration_seconds() / max(1, self.state.total_turns):.1f}s "
                    f"new_budgets={ {p.value: n for p, n in self.state.phase_budgets.items()} }"
                )

            await broadcast(self.session_id, {
                "type": "ai_text",
                "text": ai_text,
                "phase": self.state.current_phase.value,
            })

            if fillers:
                await broadcast(self.session_id, {
                    "type": "filler_alert",
                    "words": fillers,
                    "total_count": self.state.filler_count,
                })

            if self.state.should_advance() and self.state.advance_phase():
                logger.info(f"Phase → {self.state.current_phase.value}")

                # Multi-persona round: if the new phase is owned by a different
                # persona, swap state.interviewer and announce the handoff so
                # the candidate hears something like "I'll hand you over to my
                # colleague Karthik now."
                handoff_note = None
                if self.state.personas_by_phase:
                    new_persona = self.state.persona_for_phase()
                    prev_name = (self.state.interviewer or {}).get("name")
                    if new_persona and new_persona.get("name") != prev_name:
                        handoff_note = (
                            "[INTERNAL CONTROL — INTERVIEWER HANDOFF] "
                            f"You have just finished your portion of this panel interview. "
                            f"Briefly thank the candidate for their answers (one short sentence) "
                            f"and say: 'I will now hand you over to my colleague "
                            f"{new_persona['name']}, who is our {new_persona['role']}. They will "
                            f"continue the interview with you.' "
                            f"After speaking that sentence, from the NEXT turn onward you ARE "
                            f"{new_persona['name']}, a {new_persona['role']}, with this style: "
                            f"{new_persona['personality']}. Open with a short, warm self-introduction "
                            f"in your new persona's voice, then move to the next phase."
                        )
                        self.state.interviewer = new_persona

                self.gemini._system_instruction = build_system_prompt(self.state)
                await broadcast(self.session_id, {
                    "type": "phase_change",
                    "phase":      self.state.current_phase.value,
                    "turn":       self.state.total_turns,
                    "expression": _phase_to_expression(self.state.current_phase.value),
                    "speaker":    (self.state.interviewer or {}).get("name"),
                })
                if handoff_note:
                    await _speak_to_student(handoff_note)

            if self.state.total_turns % 3 == 0:
                await _sync_state_to_db(self.state)

            if self.state.is_complete():
                if self.state.extend_if_under_minimum(MIN_INTERVIEW_SEC):
                    logger.info(
                        f"Interview under {MIN_INTERVIEW_SEC // 60} min minimum — "
                        f"extending CLOSING | session={self.session_id}"
                    )
                    await _speak_to_student(
                        "[INTERNAL TIMING NOTE] We still have a few minutes left in "
                        "this interview. Ask one or two thoughtful follow-up questions, "
                        "or invite the candidate to ask you anything, before your "
                        "final summary."
                    )
                    return

                await broadcast(self.session_id, {"type": "interview_complete"})
                await asyncio.sleep(4)
                await _end_interview(self.state, reason="completed")
                if self.task:
                    await self.task.queue_frame(EndFrame())

        async def process_frame(self, frame, direction: FrameDirection):
            await super().process_frame(frame, direction)
            if isinstance(frame, TranscriptionFrame):
                self._last_user_text = frame.text or ""
            elif isinstance(frame, TextFrame) and frame.text:
                self._ai_text_parts.append(frame.text)
            elif isinstance(frame, LLMFullResponseEndFrame):
                await self._on_turn_complete()
            await self.push_frame(frame, direction)

    logger.info(f"Pipeline start | session={session_id} company={company} round={round_type}")

    past_topics, completed_count = _fetch_past_company_history(user_id, company)

    # Difficulty: user override wins; otherwise auto-derive from session count
    if difficulty_override in ("easy", "medium", "hard"):
        difficulty = difficulty_override
        logger.info(f"Difficulty override applied: {difficulty}")
    else:
        difficulty = _difficulty_from_count(completed_count)

    # Persona setup: single for normal rounds, panel-of-3 for multi_persona
    personas_by_phase: dict = {}
    if round_type == "multi_persona":
        panel = pick_multi_personas(company, seed=session_id)
        personas_by_phase = build_personas_by_phase(panel)
        # The first speaker is the warm-up persona (handles INTRO + RESUME)
        persona = panel["warmup"]
        logger.info(
            f"Multi-persona panel: warmup={panel['warmup']['name']}, "
            f"technical={panel['technical']['name']}, hr={panel['hr']['name']}"
        )
    else:
        persona = pick_interviewer(company, seed=session_id)
        logger.info(f"Persona={persona['name']} ({persona['role']})")

    logger.info(
        f"Session start | prior_completed={completed_count} → difficulty={difficulty} | "
        f"past_topics={len(past_topics)} | round={round_type}"
    )

    state = create_session_state(
        session_id=session_id,
        user_id=user_id,
        company=company,
        round_type=round_type,
        resume_text=resume_text,
        past_topics=past_topics,
        interviewer=persona,
        personas_by_phase=personas_by_phase,
        difficulty_level=difficulty,
    )

    try:
        supabase_admin.table("sessions").update({
            "status": "active",
            "started_at": "now()",
        }).eq("id", session_id).execute()
    except Exception as e:
        logger.error(f"Failed to mark session active: {e}")

    initial_prompt = build_system_prompt(state)

    transport = DailyTransport(
        room_url,
        room_token,
        "InterviewPhodo AI",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
            camera_out_enabled=False,
            # stop_secs is how long we wait in silence before ending the
            # student's turn. 2.5s lets the candidate think mid-answer
            # without the AI cutting them off.
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=2.5)),
        ),
    )

    gemini = GeminiLiveLLMService(
        api_key=settings.google_api_key,
        settings=GeminiLiveLLMService.Settings(
            model="models/gemini-3.1-flash-live-preview",
            voice="Charon",
            modalities=GeminiModalities.AUDIO,
        ),
        system_instruction=initial_prompt,
        transcribe_user_audio=True,
    )

    # Context holds the conversation history. We seed it with one user message
    # so Gemini speaks the greeting first (inference_on_context_initialization).
    context = LLMContext(messages=[
        {"role": "user", "content": "Please introduce yourself and start the interview now."}
    ])
    context_aggregator = LLMContextAggregatorPair(context)

    turn_processor = InterviewTurnProcessor(state=state, session_id=session_id, gemini=gemini)

    task = PipelineTask(
        Pipeline([
            transport.input(),
            context_aggregator.user(),
            gemini,
            turn_processor,
            transport.output(),
            context_aggregator.assistant(),
        ]),
        params=PipelineParams(allow_interruptions=True, enable_metrics=True),
    )
    turn_processor.task = task

    # Signal set the moment the first non-bot participant joins.
    # The no-show watchdog waits on this; if nothing fires within
    # NO_SHOW_TIMEOUT_SEC, the session ends without charging a credit.
    NO_SHOW_TIMEOUT_SEC = 5 * 60
    participant_joined = asyncio.Event()

    @transport.event_handler("on_first_participant_joined")
    async def on_first_join(transport, participant):
        """When the student joins:
        1. Mark the no-show watchdog satisfied.
        2. Deduct one session credit (the user actually showed up).
        3. Fire LLMRunFrame so Gemini speaks the seeded greeting.
        """
        participant_joined.set()
        state.joined_at = time.time()
        logger.info(f"Student joined: {participant.get('id', 'unknown')} — triggering greeting")
        try:
            current = supabase_admin.table("users").select(
                "sessions_used"
            ).eq("id", user_id).single().execute()
            new_used = (current.data["sessions_used"] or 0) + 1
            supabase_admin.table("users").update({
                "sessions_used": new_used,
            }).eq("id", user_id).execute()
            logger.info(f"Credit deducted | user={user_id} sessions_used={new_used}")
        except Exception as e:
            logger.error(f"Failed to deduct credit: {e}")
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_participant_left")
    async def on_left(transport, participant, reason):
        logger.info(f"Student left: {participant.get('id', 'unknown')}")
        await broadcast(session_id, {"type": "session_ended", "reason": "student_left"})
        await _end_interview(state, reason="student_left")
        await task.queue_frame(EndFrame())

    async def no_show_watchdog():
        """End the session if no student joins within NO_SHOW_TIMEOUT_SEC.
        Credit is NOT deducted in this path — the user effectively gets a free
        cancellation."""
        try:
            await asyncio.wait_for(participant_joined.wait(), timeout=NO_SHOW_TIMEOUT_SEC)
            logger.debug("No-show watchdog satisfied; participant joined in time")
        except asyncio.TimeoutError:
            logger.warning(
                f"No-show: session {session_id} ending after "
                f"{NO_SHOW_TIMEOUT_SEC}s with no participant. Credit NOT deducted."
            )
            try:
                supabase_admin.table("sessions").update({
                    "status": "abandoned",
                    "ended_at": "now()",
                }).eq("id", session_id).execute()
            except Exception as db_err:
                logger.error(f"Failed to mark session abandoned: {db_err}")
            await broadcast(session_id, {"type": "session_ended", "reason": "no_show"})
            await task.queue_frame(EndFrame())

    watchdog_task = asyncio.create_task(no_show_watchdog())

    # ---- Time-aware announcements -------------------------------------------------
    # Interviews run 25–30 min from student join. The AI:
    #   25:00 → audibly announce "we have about 5 minutes left"
    #   28:30 → force-jump to CLOSING phase if not already there
    #   29:57 → short goodbye (3 sec before hard cap), then end gracefully
    # All three are gated on the student actually being in the call.

    async def _speak_to_student(internal_note: str):
        """Inject a synthetic user-side note into the LLM context and trigger
        Gemini to respond. This is how we make the AI proactively say
        something time-driven."""
        context.messages.append({"role": "user", "content": internal_note})
        await task.queue_frames([LLMRunFrame()])

    async def time_watchdog():
        """Wall-clock interview pacing — separate from FSM turn budgets.
        All target offsets below are measured from the moment the student
        actually joined (so the 5-min no-show grace period doesn't eat into
        interview time)."""
        try:
            await participant_joined.wait()
            loop_start = asyncio.get_event_loop().time()

            async def sleep_until(target_offset: float):
                remaining = target_offset - (asyncio.get_event_loop().time() - loop_start)
                if remaining > 0:
                    await asyncio.sleep(remaining)

            # 25:00 — five minutes left in the 30-min window
            await sleep_until(WARN_5MIN_AT)
            if state.is_complete():
                return
            logger.info("Time watchdog: 5-minute warning")
            await _speak_to_student(
                "[INTERNAL TIMING NOTE — speak this naturally to the candidate now] "
                "We have about 5 minutes remaining in this interview. Briefly tell "
                "the candidate this, wrap up your current question if any, and move "
                "on to your final 1-2 questions before closing."
            )

            # 28:30 — force jump to CLOSING phase
            await sleep_until(FORCE_CLOSE_AT)
            if not state.is_complete() and state.current_phase != InterviewPhase.CLOSING:
                logger.info("Time watchdog: forcing CLOSING phase")
                state.jump_to_phase(InterviewPhase.CLOSING)
                gemini._system_instruction = build_system_prompt(state)
                await broadcast(session_id, {
                    "type": "phase_change",
                    "phase": state.current_phase.value,
                    "turn":  state.total_turns,
                    "expression": _phase_to_expression(state.current_phase.value),
                })
                await _speak_to_student(
                    "[INTERNAL TIMING NOTE — time to wrap up] "
                    "Time is almost up. Deliver your final performance report now, "
                    "concisely (about 60 seconds total). Hit all 6 closing points: "
                    "score, top 3 strengths, top 3 improvements, speech quality, "
                    "honest verdict, next steps."
                )

            # 29:57 — short goodbye, then hard end at 30:00
            await sleep_until(GOODBYE_AT)
            logger.info("Time watchdog: speaking final goodbye")
            await _speak_to_student(
                "[INTERNAL TIMING NOTE — final goodbye, one short line only] "
                "Say exactly this in your voice and tone: "
                "'Goodbye, all the best!' Then stop speaking."
            )
            await sleep_until(MAX_INTERVIEW_SEC)
            logger.info("Time watchdog: ending pipeline at hard cap")
            await _end_interview(state, reason="time_capped")
            await task.queue_frame(EndFrame())
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Time watchdog error: {e}")

    time_watchdog_task = asyncio.create_task(time_watchdog())

    # Count this pipeline as live right before we run it, so it is always
    # paired with the _register_pipeline_end() in the finally below.
    await _register_pipeline_start()

    runner = PipelineRunner()
    try:
        await runner.run(task)
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        await _end_interview(state, reason="error")
    finally:
        if not watchdog_task.done():
            watchdog_task.cancel()
        if not time_watchdog_task.done():
            time_watchdog_task.cancel()
        remove_session_state(session_id)
        remove_session_connections(session_id)
        # Daily's native context is process-wide. Only deinit when no other
        # session is still live — see _register_pipeline_end(). Deinit-ing
        # while another interview is active crashes the process (exit 134).
        await _register_pipeline_end()
        logger.info(f"Pipeline ended | session={session_id}")

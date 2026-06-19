"""
Pipecat real-time interview pipeline — interviewphodo.com

Pipecat is imported lazily inside run_interview_pipeline() so the FastAPI app
can start on machines where pipecat-ai is not installed yet (e.g. Python 3.14).
Use Python 3.11 or 3.12 for full interview pipeline support.
"""

import asyncio
import logging

from services.interview_fsm import InterviewState, create_session_state, remove_session_state
from services.speech_analyser import detect_filler_words
from prompts.fsm_prompt_builder import build_system_prompt
from services.avatar_broadcaster import broadcast, remove_session_connections
from database.supabase_client import supabase_admin
from config import settings

logger = logging.getLogger(__name__)


async def _sync_state_to_db(state: InterviewState):
    """Persist FSM state to Supabase every few turns."""
    try:
        supabase_admin.table("sessions").update(
            state.to_db_dict()
        ).eq("id", state.session_id).execute()
    except Exception as e:
        logger.error(f"DB sync error: {e}")


async def _end_interview(state: InterviewState, reason: str = "completed"):
    """Clean up after interview ends — update DB and generate report."""
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
    """Maps interview phase to avatar facial expression hint."""
    return {
        "intro":         "warm",
        "resume_review": "attentive",
        "technical_qa":  "serious",
        "behavioral":    "curious",
        "hr_round":      "formal",
        "candidate_qa":  "open",
        "closing":       "reflective",
    }.get(phase, "neutral")


async def run_interview_pipeline(
    room_url: str,
    room_token: str,
    session_id: str,
    user_id: str,
    company: str,
    round_type: str,
    resume_text: str = "",
):
    """
    Main pipeline runner. Called as asyncio background task from /api/sessions/start.
    Runs until interview completes or student leaves.
    """
    try:
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.runner import PipelineRunner
        from pipecat.pipeline.task import PipelineTask, PipelineParams
        from pipecat.transports.services.daily import DailyTransport, DailyParams
        from pipecat.services.google import GeminiMultimodalLiveLLMService, InputParams
        from pipecat.frames.frames import EndFrame
    except ImportError as e:
        logger.error(
            "Pipecat is not installed. Use Python 3.11 or 3.12 and: "
            "pip install 'pipecat-ai[daily,google]==0.0.47'"
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
            "Pipecat not available. Install with Python 3.11/3.12 — see README."
        ) from e

    logger.info(f"Pipeline start | session={session_id} company={company} round={round_type}")

    state = create_session_state(
        session_id=session_id,
        user_id=user_id,
        company=company,
        round_type=round_type,
        resume_text=resume_text,
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
            camera_out_enabled=False,
            transcription_enabled=True,
        ),
    )

    gemini = GeminiMultimodalLiveLLMService(
        api_key=settings.google_api_key,
        model="gemini-3.1-flash-live-preview",
        params=InputParams(
            voice="Charon",
            language="en-IN",
        ),
        system_instruction=initial_prompt,
    )

    pipeline = Pipeline([
        transport.input(),
        gemini,
        transport.output(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(allow_interruptions=True),
    )

    @transport.event_handler("on_participant_left")
    async def on_left(transport, participant, reason):
        logger.info(f"Student left: {participant['id']}")
        await broadcast(session_id, {"type": "session_ended", "reason": "student_left"})
        await _end_interview(state, reason="student_left")
        await task.queue_frame(EndFrame())

    @gemini.event_handler("on_llm_full_completion")
    async def on_response(service, messages, completion):
        """After each Gemini response: record turn, detect fillers, check phase transition."""
        if not messages:
            return

        ai_text = completion if isinstance(completion, str) else ""
        student_text = ""

        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            student_text = part.get("text", "")
                            break
                else:
                    student_text = str(content)
                break

        fillers = detect_filler_words(student_text)
        state.record_turn(
            student_text=student_text,
            ai_text=ai_text,
            filler_words=fillers,
        )

        await broadcast(session_id, {
            "type": "ai_text",
            "text": ai_text,
            "phase": state.current_phase.value,
        })

        if fillers:
            await broadcast(session_id, {
                "type": "filler_alert",
                "words": fillers,
                "total_count": state.filler_count,
            })

        if state.should_advance():
            if state.advance_phase():
                logger.info(f"Phase → {state.current_phase.value}")
                new_prompt = build_system_prompt(state)
                try:
                    await service.update_settings({"system_instruction": new_prompt})
                except Exception as e:
                    logger.warning(f"Could not update system instruction: {e}")

                await broadcast(session_id, {
                    "type": "phase_change",
                    "phase": state.current_phase.value,
                    "turn": state.total_turns,
                    "expression": _phase_to_expression(state.current_phase.value),
                })

        if state.total_turns % 3 == 0:
            await _sync_state_to_db(state)

        if state.is_complete():
            await broadcast(session_id, {"type": "interview_complete"})
            await asyncio.sleep(4)
            await _end_interview(state, reason="completed")
            await task.queue_frame(EndFrame())

    runner = PipelineRunner()
    try:
        await runner.run(task)
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        await _end_interview(state, reason="error")
    finally:
        remove_session_state(session_id)
        remove_session_connections(session_id)
        logger.info(f"Pipeline ended | session={session_id}")

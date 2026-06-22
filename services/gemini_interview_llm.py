"""
Gemini Live wrapper for 25–30 minute interviews.

Google's Live API limits each WebSocket connection to ~10 minutes. The server
sends a goAway message before disconnecting; we reconnect with session
resumption. Do NOT proactively disconnect on a timer — that breaks the live
audio path unless realtime input is re-enabled.

See: https://ai.google.dev/gemini-api/docs/live-api/session-management
"""

from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, Optional

from google.genai.types import Content, Part
from loguru import logger

from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService

GEMINI_LIVE_MODEL = "models/gemini-3.1-flash-live-preview"


class InterviewGeminiLiveLLMService(GeminiLiveLLMService):
    """Gemini Live with goAway reconnects and post-resume audio recovery."""

    def __init__(self, *args, on_reconnected: Optional[Callable[[], Awaitable[None]]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_reconnected = on_reconnected
        self._session_ready_event = asyncio.Event()
        self._reconnect_lock = asyncio.Lock()

    @property
    def _system_instruction(self) -> Optional[str]:
        return self._system_instruction_from_init

    @_system_instruction.setter
    def _system_instruction(self, value: Optional[str]) -> None:
        """Pipeline updates the FSM prompt here — must map to pipecat's init field."""
        self._system_instruction_from_init = value

    def connection_age_seconds(self) -> float:
        if not self._connection_start_time:
            return 0.0
        return time.time() - self._connection_start_time

    async def _wait_session_ready(self, timeout: float = 20.0) -> bool:
        try:
            await asyncio.wait_for(self._session_ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.error(f"Gemini Live: session not ready after {timeout:.0f}s")
            return False

    async def _ensure_live_after_resume(self) -> None:
        """After session resumption, pipecat skips _create_initial_response — re-enable audio."""
        if self._context is not None and not self._ready_for_realtime_input:
            self._ready_for_realtime_input = True
            logger.info("Gemini Live: realtime input re-enabled after session resume")

    async def _reconnect(self) -> None:
        self._session_ready_event.clear()
        await super()._reconnect()
        await self._wait_session_ready()
        await self._ensure_live_after_resume()

    async def reconnect_for_continuity(self) -> None:
        """Reconnect using the latest session resumption handle (goAway / errors only)."""
        async with self._reconnect_lock:
            if self._disconnecting:
                return
            has_handle = bool(self._session_resumption_handle)
            logger.info(
                f"Gemini Live reconnect | age={self.connection_age_seconds():.0f}s "
                f"resumption={'yes' if has_handle else 'no'}"
            )
            await self._reconnect()
            if self._on_reconnected:
                try:
                    await self._on_reconnected()
                except Exception as e:
                    logger.error(f"Post-reconnect hook failed: {e}")

    async def send_control_turn(self, text: str, *, wait_ready: bool = True) -> bool:
        """Send an internal control message and trigger a spoken response.

        LLMRunFrame + context append does NOT reach Gemini Live after resumption;
        we must use send_client_content directly.
        """
        if self._disconnecting:
            return False
        if wait_ready:
            if not self._session:
                ok = await self._wait_session_ready(timeout=12.0)
                if not ok:
                    return False
            if not self._ready_for_realtime_input:
                await self._ensure_live_after_resume()

        if not self._session:
            return False

        await self.start_ttfb_metrics()
        try:
            turn = Content(role="user", parts=[Part(text=text)])
            await self._session.send_client_content(turns=[turn], turn_complete=True)
            if self._is_gemini_3:
                await self._session.send_realtime_input(text=" ")
            return True
        except Exception as e:
            logger.error(f"send_control_turn failed: {e}")
            return False

    async def _handle_session_ready(self, session) -> None:
        await super()._handle_session_ready(session)
        self._session_ready_event.set()
        await self._ensure_live_after_resume()

    async def _dispatch_server_message(self, message) -> None:
        """Process one LiveServerMessage (mirrors pipecat 0.0.108 handler body)."""
        sc = message.server_content
        if sc and sc.interrupted:
            logger.debug("Gemini VAD: interrupted signal received")
            await self.broadcast_interruption()
        if sc and sc.model_turn:
            await self._handle_msg_model_turn(message)
        if sc and sc.input_transcription:
            await self._handle_msg_input_transcription(message)
        if sc and sc.output_transcription:
            await self._handle_msg_output_transcription(message)
        if (
            sc
            and sc.grounding_metadata
            and not sc.model_turn
            and not sc.output_transcription
        ):
            await self._handle_msg_grounding_metadata(message)
        if sc and sc.turn_complete:
            if not message.usage_metadata:
                logger.warning("Received turn_complete without usage_metadata")
            await self._handle_msg_turn_complete(message)
            if message.usage_metadata:
                await self._handle_msg_usage_metadata(message)
        if message.tool_call:
            await self._handle_msg_tool_call(message)
        if message.session_resumption_update:
            self._handle_msg_resumption_update(message)

    async def _connection_task_handler(self, config):
        async with self._client.aio.live.connect(
            model=self._settings.model, config=config
        ) as session:
            logger.info("Connected to Gemini Live (interview session)")
            self._connection_start_time = time.time()
            await self._handle_session_ready(session)

            while True:
                try:
                    turn = self._session.receive()
                    async for message in turn:
                        self._check_and_reset_failure_counter()

                        if message.go_away:
                            time_left = getattr(message.go_away, "time_left", None)
                            logger.warning(
                                f"Gemini goAway received (time_left={time_left}) — "
                                "reconnecting with session resumption"
                            )
                            await self.reconnect_for_continuity()
                            return

                        await self._dispatch_server_message(message)
                except Exception as e:
                    if not self._disconnecting:
                        should_reconnect = await self._handle_connection_error(e)
                        if should_reconnect:
                            await self.reconnect_for_continuity()
                            return
                    break


def default_interview_gemini_settings(**overrides) -> GeminiLiveLLMService.Settings:
    """Live settings tuned for 25–30 min audio interviews."""
    base = dict(
        voice="Charon",
        temperature=0.7,
        context_window_compression={
            "enabled": True,
            "trigger_tokens": 28000,
        },
    )
    base.update(overrides)
    return GeminiLiveLLMService.Settings(**base)

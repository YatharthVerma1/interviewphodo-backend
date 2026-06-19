# services/avatar_broadcaster.py
"""
Avatar Broadcaster — interviewphodo.com
=========================================
Manages one WebSocket connection per active interview session.
The pipeline calls broadcast() after every Gemini response.
The frontend Three.js avatar listens and reacts.

Events pushed to frontend:
  phase_change    → update phase progress bar + switch avatar expression
  ai_text         → display subtitle text beneath avatar
  filler_alert    → update live filler word counter
  interview_complete → navigate to report page
  session_ended   → handle student disconnect
"""

import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# session_id → list of connected WebSockets (list for multiple tabs)
_connections: dict[str, list[WebSocket]] = {}


def register_connection(session_id: str, ws: WebSocket):
    """Register a new WebSocket for a session."""
    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(ws)
    logger.info(f"WebSocket registered | session={session_id} total={len(_connections[session_id])}")


def unregister_connection(session_id: str, ws: WebSocket):
    """Remove a WebSocket when frontend disconnects."""
    if session_id in _connections:
        _connections[session_id] = [c for c in _connections[session_id] if c != ws]
        if not _connections[session_id]:
            del _connections[session_id]
    logger.info(f"WebSocket unregistered | session={session_id}")


def remove_session_connections(session_id: str):
    """Remove all connections for a session when pipeline ends."""
    _connections.pop(session_id, None)


async def broadcast(session_id: str, event: dict):
    """
    Push an event JSON to all WebSocket connections for this session.
    Called from interview_pipeline.py after each Gemini response.

    Event shapes:
    {"type": "phase_change",  "phase": "technical_qa", "expression": "serious", "turn": 5}
    {"type": "ai_text",       "text": "Tell me about your project.", "phase": "resume_review"}
    {"type": "filler_alert",  "words": ["um", "basically"], "total_count": 4}
    {"type": "interview_complete"}
    {"type": "session_ended", "reason": "student_left"}
    """
    connections = _connections.get(session_id, [])
    if not connections:
        return

    payload = json.dumps(event)
    dead = []

    for ws in connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    # Clean up broken connections
    for ws in dead:
        unregister_connection(session_id, ws)

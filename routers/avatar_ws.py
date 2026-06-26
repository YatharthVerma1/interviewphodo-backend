# routers/avatar_ws.py
"""
Avatar WebSocket Router — interviewphodo.com
=============================================
Frontend Three.js avatar connects here at interview start.
Receives real-time push events from the Pipecat pipeline via avatar_broadcaster.

Connection URL (frontend):
  ws://your-backend.railway.app/ws/avatar/{session_id}?token=<supabase-jwt>

Message types received by frontend:
  phase_change      → update InterviewPhaseBar component + switch avatar expression
  ai_text           → display subtitle text under avatar face
  filler_alert      → increment live filler word counter on HUD
  interview_complete → redirect to /report/{session_id}
  session_ended     → show "session ended" message
  ping              → keep-alive (frontend should pong back)
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from database.supabase_client import fetch_one, supabase_admin
from services.avatar_broadcaster import register_connection, unregister_connection

router  = APIRouter()
logger  = logging.getLogger(__name__)


@router.websocket("/avatar/{session_id}")
async def avatar_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),    # Supabase JWT passed as query param
):
    """
    WebSocket endpoint for the frontend Three.js avatar.
    Frontend connects immediately after session start.
    Stays open for the entire interview duration.
    """

    # 1. Validate Supabase JWT before accepting connection
    try:
        auth_response = supabase_admin.auth.get_user(token)
        user_id = auth_response.user.id
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # 2. Verify session belongs to this user
    try:
        session = fetch_one(
            supabase_admin.table("sessions")
            .select("user_id, status")
            .eq("id", session_id)
        )
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return
        if session["user_id"] != user_id:
            await websocket.close(code=4003, reason="Forbidden")
            return
        if session["status"] == "completed":
            await websocket.close(code=4000, reason="Session already completed")
            return
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        await websocket.close(code=4500, reason="Server error")
        return

    # 3. Accept and register connection
    await websocket.accept()
    register_connection(session_id, websocket)
    logger.info(f"Avatar WS connected | session={session_id} user={user_id}")

    # 4. Send initial state so frontend can sync immediately on connect
    await websocket.send_json({
        "type":  "connected",
        "session_id": session_id,
        "message": "Avatar WebSocket connected. Interview events will stream here.",
    })

    # 5. Keep connection alive — listen for pings from frontend
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            # Frontend can also send posture events via this WebSocket
            # as an alternative to the REST POST endpoint
            elif data.startswith("{"):
                import json
                try:
                    event = json.loads(data)
                    if event.get("type") == "posture_event":
                        from services.interview_fsm import get_session_state
                        state = get_session_state(session_id)
                        if state:
                            state.add_posture_event(
                                event.get("event_type", "unknown"),
                                event.get("message", ""),
                            )
                    elif event.get("type") == "eye_contact_sample":
                        from services.interview_fsm import get_session_state
                        state = get_session_state(session_id)
                        if state and event.get("score") is not None:
                            state.add_eye_contact_sample(int(event["score"]))
                except Exception:
                    pass  # Ignore malformed messages

    except WebSocketDisconnect:
        logger.info(f"Avatar WS disconnected | session={session_id}")
    except Exception as e:
        logger.error(f"Avatar WS error: {e}")
    finally:
        unregister_connection(session_id, websocket)

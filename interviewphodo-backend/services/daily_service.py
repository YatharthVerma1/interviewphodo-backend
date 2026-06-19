import time
import httpx
from config import settings
from services.interview_timing import DAILY_ROOM_SEC

DAILY_BASE = "https://api.daily.co/v1"
DAILY_HEADERS = {
    "Authorization": f"Bearer {settings.daily_api_key}",
    "Content-Type": "application/json",
}


async def create_interview_room(session_id: str) -> dict:
    """Create a private Daily.co room + tokens for AI bot and student.

    Returns:
        url    -> URL the student opens (already includes their meeting token)
        name   -> Daily room name
        token  -> AI bot's owner token (used by Pipecat to join)
    """
    room_name = f"phodo-{session_id[:12]}"
    # Hard ceiling for the Daily room (and AI bot + student tokens).
    # Interview runs 25–30 min; room expires slightly after max so goodbye audio
    # can finish without Daily cutting the call mid-sentence.
    expiry = int(time.time()) + DAILY_ROOM_SEC

    async with httpx.AsyncClient() as client:
        room_res = await client.post(
            f"{DAILY_BASE}/rooms",
            headers=DAILY_HEADERS,
            json={
                "name": room_name,
                "privacy": "private",
                "properties": {
                    "exp": expiry,
                    "max_participants": 2,
                    "enable_chat": False,
                    "enable_screenshare": False,
                },
            },
        )
        room_res.raise_for_status()
        room = room_res.json()

        # AI bot token — owner privileges (used by Pipecat)
        bot_token_res = await client.post(
            f"{DAILY_BASE}/meeting-tokens",
            headers=DAILY_HEADERS,
            json={"properties": {
                "room_name": room_name,
                "is_owner": True,
                "user_name": "InterviewPhodo AI",
                "exp": expiry,
            }},
        )
        bot_token_res.raise_for_status()
        bot_token = bot_token_res.json()["token"]

        # Student token — regular participant
        student_token_res = await client.post(
            f"{DAILY_BASE}/meeting-tokens",
            headers=DAILY_HEADERS,
            json={"properties": {
                "room_name": room_name,
                "is_owner": False,
                "user_name": "Student",
                "exp": expiry,
            }},
        )
        student_token_res.raise_for_status()
        student_token = student_token_res.json()["token"]

    return {
        "url":         room["url"],                        # bare URL (for AI bot)
        "student_url": f"{room['url']}?t={student_token}", # tokenized URL (for student)
        "name":        room["name"],
        "token":       bot_token,
    }


async def delete_room(room_name: str) -> bool:
    async with httpx.AsyncClient() as client:
        res = await client.delete(
            f"{DAILY_BASE}/rooms/{room_name}",
            headers=DAILY_HEADERS,
        )
        return res.status_code == 200

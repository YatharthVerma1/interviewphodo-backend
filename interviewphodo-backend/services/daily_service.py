import time
import httpx
from config import settings

DAILY_BASE = "https://api.daily.co/v1"
DAILY_HEADERS = {
    "Authorization": f"Bearer {settings.daily_api_key}",
    "Content-Type": "application/json",
}


async def create_interview_room(session_id: str) -> dict:
    """
    Creates a private Daily.co room. Expires after 45 minutes.
    Returns: {"url": str, "name": str, "token": str}
    The token is used by the Pipecat AI bot to join the room.
    The url is sent to the frontend so the student can join.
    """
    room_name = f"phodo-{session_id[:12]}"
    expiry = int(time.time()) + (45 * 60)

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

        token_res = await client.post(
            f"{DAILY_BASE}/meeting-tokens",
            headers=DAILY_HEADERS,
            json={
                "properties": {
                    "room_name": room_name,
                    "is_owner": True,
                    "user_name": "InterviewPhodo AI",
                    "exp": expiry,
                }
            },
        )
        token_res.raise_for_status()
        token = token_res.json()

    return {
        "url":  room["url"],
        "name": room["name"],
        "token": token["token"],
    }


async def delete_room(room_name: str) -> bool:
    async with httpx.AsyncClient() as client:
        res = await client.delete(
            f"{DAILY_BASE}/rooms/{room_name}",
            headers=DAILY_HEADERS,
        )
        return res.status_code == 200

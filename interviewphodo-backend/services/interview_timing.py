"""
Interview wall-clock timing — interviewphodo.com

Every interview runs at least MIN_INTERVIEW_SEC and at most MAX_INTERVIEW_SEC,
measured from when the student joins the Daily room.

Daily.co room expiry is MAX + a small buffer so the goodbye can finish.
"""

# Student-facing interview window (seconds from join)
MIN_INTERVIEW_SEC = 25 * 60   # 25:00 — do not end naturally before this
MAX_INTERVIEW_SEC = 30 * 60   # 30:00 — hard stop

# Daily room + token expiry (slightly above max so goodbye audio can play out)
DAILY_ROOM_SEC = MAX_INTERVIEW_SEC + 60  # 31:00

# Time watchdog milestones (offsets from student join)
WARN_5MIN_AT   = MIN_INTERVIEW_SEC          # 25:00 — "about 5 minutes left"
FORCE_CLOSE_AT = MAX_INTERVIEW_SEC - 90     # 28:30 — force CLOSING + verbal report
GOODBYE_AT     = MAX_INTERVIEW_SEC - 3      # 29:57 — short goodbye, then end

# FSM rebalance target (middle of the window)
REBALANCE_TARGET_SEC = 27 * 60

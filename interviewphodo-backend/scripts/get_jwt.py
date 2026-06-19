#!/usr/bin/env python3
"""Get a Supabase JWT for API testing. Run from interviewphodo-backend/."""

import getpass
import json
import sys
from pathlib import Path

# Allow running as: python scripts/get_jwt.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from config import settings


def main():
    if not settings.supabase_configured:
        print("Error: set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
        sys.exit(1)

    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    response = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30,
    )

    if response.status_code != 200:
        print("Login failed:", response.text)
        sys.exit(1)

    data = response.json()
    token = data["access_token"]
    print("\n--- Copy this token (without 'Bearer') into Swagger Authorize ---\n")
    print(token)
    print("\n--- Or use curl ---\n")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/api/auth/me')


if __name__ == "__main__":
    main()


import os
import uuid
import time
import secrets
import warnings
from datetime import datetime
from collections import defaultdict

warnings.filterwarnings("ignore")

from flask import Flask, request, jsonify, session, render_template_string
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

# ==========================================
# CONFIGURATION
# ==========================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

if not FLASK_SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY is missing from .env")

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Secure session cookie settings
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("RENDER")),
    PERMANENT_SESSION_LIFETIME=86400
)

client = genai.Client(api_key=GEMINI_API_KEY)

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

PERSONALITY = """
You are NOVA, an AI assistant created by NV STUDIOS.

CORE RULES:
- Prioritize human life and safety.
- Never facilitate harm or illegal activity.
- Be helpful, accurate and friendly.
- Never invent information.

DEFAULT MODE:
- Professional and friendly.
- Use proper grammar.
- Explain clearly.

GET MODE:
- Talk like Gen Z / Gen Alpha.
- Keep answers short, usually 1-2 lines.
- Occasionally say bro, twin and homie.
- Be funny and slightly corny.
- Use emojis sparingly: 😭 ✌️ 🫩 🥀 💔
- Never use 😎.
- You can disagree with the user.

Safety and accuracy always come first.
"""

# ==========================================
# CHAT STORAGE
# ==========================================

# In-memory storage: conversations reset when
# the server restarts.

chats = {}

MAX_CHATS_PER_USER = 5
MAX_TOTAL_CHATS = 500

# Basic in-memory rate limiting
request_history = defaultdict(list)

MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_HOUR = 60


def get_owner_id():
    """Give each browser session its own identity."""

    session.permanent = True

    if "nova_owner_id" not in session:
        session["nova_owner_id"] = secrets.token_urlsafe(32)

    return session["nova_owner_id"]


def is_rate_limited(owner_id):
    """Limit excessive requests per browser session."""

    now = time.time()

    events = request_history[owner_id]

    # Keep only requests from the last hour
    events[:] = [
        timestamp for timestamp in events
        if now - timestamp < 3600
    ]

    recent_minute = [
        timestamp for timestamp in events
        if now - timestamp < 60
    ]

    if len(recent_minute) >= MAX_REQUESTS_PER_MINUTE:
        return True

    if len(events) >= MAX_REQUESTS_PER_HOUR:
        return True

    events.append(now)

    return False


def create_chat(model=PRIMARY_MODEL):
    return client.chats.create(
        model=model,
        config={"system_instruction": PERSONALITY}
    )


def remove_old_chats(owner_id):
    """Keep the number of conversations under control."""

    user_chats = [
        (conversation_id, data)
        for conversation_id, data in chats.items()
        if data["owner_id"] == owner_id
    ]

    user_chats.sort(
        key=lambda item: item[1]["created_at"]
    )

    while len(user_chats) >= MAX_CHATS_PER_USER:
        conversation_id, _ = user_chats.pop(0)
        chats.pop(conversation_id, None)

    # Global storage limit
    while len(chats) >= MAX_TOTAL_CHATS:
        oldest_id = min(
            chats,
            key=lambda key: chats[key]["created_at"]
        )
        chats.pop(oldest_id, None)

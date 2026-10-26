"""Settings loaded from .env, in one place."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- AI provider: "gemini" or "claude". If not set, use whichever key is filled in.
GEMINI_API_KEY = env("GEMINI_API_KEY")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
AI_PROVIDER = env("AI_PROVIDER").lower() or ("gemini" if GEMINI_API_KEY and not ANTHROPIC_API_KEY else "claude")

if AI_PROVIDER == "gemini":
    AI_API_KEY = GEMINI_API_KEY
    AI_MODEL = env("GEMINI_MODEL", "gemini-3.5-flash-lite")
else:
    AI_PROVIDER = "claude"
    AI_API_KEY = ANTHROPIC_API_KEY
    AI_MODEL = env("CLAUDE_MODEL", "claude-haiku-5-5")

# No key for the chosen provider -> mock mode (fake answers), so the app still runs
MOCK_AI = env("MOCK_AI", "0") == "1" or not AI_API_KEY

TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = env("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

PORT = int(env("PORT", "8000"))
MIN_CONFIDENCE = float(env("MIN_CONFIDENCE", "0.6"))

DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"

# Languages offered in the pilot. code -> name the model understands
LANGUAGES = {
    "en": "English",
    "ar": "Arabic",
    "hi": "Hindi",
    "ur": "Urdu",
    "tl": "Tagalog",
    "bn": "Bengali",
    "ml": "Malayalam",
}

"""Settings loaded from .env, in one place."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5").strip()
MOCK_AI = os.getenv("MOCK_AI", "0").strip() == "1" or not ANTHROPIC_API_KEY

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886").strip()

PORT = int(os.getenv("PORT", "8000"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.6"))

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

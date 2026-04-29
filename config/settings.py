"""
config/settings.py
------------------
Central configuration for Facemark.
All other modules import from here — never read .env directly elsewhere.
"""

from dotenv import load_dotenv
import os

# Load .env file from project root
load_dotenv()

# ── Organisation ──────────────────────────────────────────────────────────────
ORG_NAME        = os.getenv("ORG_NAME", "My Organisation")
MEMBER_LABEL    = os.getenv("MEMBER_LABEL", "member")   # learner / employee / student

# ── Face Recognition ──────────────────────────────────────────────────────────
FACE_TOLERANCE  = float(os.getenv("FACE_TOLERANCE", 0.5))
FACE_MODEL      = os.getenv("FACE_MODEL", "hog")         # hog = CPU, cnn = GPU
SCAN_INTERVAL   = int(os.getenv("SCAN_INTERVAL", 2))     # seconds between scans

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH         = os.getenv("DB_PATH", "database/facemark.db")
ENCODINGS_PATH  = os.getenv("ENCODINGS_PATH", "encodings/face_encodings.pkl")

# ── API ───────────────────────────────────────────────────────────────────────
API_HOST        = os.getenv("API_HOST", "0.0.0.0")
API_PORT        = int(os.getenv("API_PORT", 8000))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
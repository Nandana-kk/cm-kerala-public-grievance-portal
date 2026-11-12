import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration settings."""
    # Flask Secret Key for session signing
    SECRET_KEY = os.getenv("SECRET_KEY", "cm-kerala-secure-dev-session-key-2026")
    
    # MySQL Database Configuration
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3307))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "cm_kerala_portal")
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB maximum upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "doc", "docx"}
    
    # Google Gemini AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Session security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

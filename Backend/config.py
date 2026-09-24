import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH, override=False)

STANDARDIZED_KEYS = {
    "GROQ_API_KEY": ["GroqAPIKey", "GROQ_API_KEY"],
    "COHERE_API_KEY": ["CohereAPIKey", "COHERE_API_KEY"],
    "HUGGINGFACE_API_KEY": ["HUGGINGFACE_API_KEY"],
    "WEATHER_API_KEY": ["WEATHER_API_KEY"],
    "ELEVENLABS_API_KEY": ["ELEVENLABS_API_KEY"],
    "ELEVENLABS_VOICE_ID": ["ELEVENLABS_VOICE_ID"],
    "SUPABASE_URL": ["SUPABASE_URL"],
    "SUPABASE_KEY": ["SUPABASE_KEY"],
    "SUPABASE_SERVICE_ROLE_KEY": ["SUPABASE_SERVICE_ROLE_KEY"],
    "DATABASE_URL": ["DATABASE_URL"],
    "SECRET_KEY": ["SECRET_KEY"],
    "USERNAME": ["USERNAME", "Username"],
    "ASSISTANT_NAME": ["ASSISTANT_NAME", "Assistantname"],
    "INPUT_LANGUAGE": ["INPUT_LANGUAGE", "InputLanguage"],
    "ASSISTANT_VOICE": ["ASSISTANT_VOICE", "AssistantVoice"],
    "SMTP_HOST": ["SMTP_HOST"],
    "SMTP_PORT": ["SMTP_PORT"],
    "SMTP_USERNAME": ["SMTP_USERNAME"],
    "SMTP_PASSWORD": ["SMTP_PASSWORD"],
    "SMTP_FROM": ["SMTP_FROM"],
    "SMTP_USE_SSL": ["SMTP_USE_SSL"],
    "PORT": ["PORT"],
    "HOST": ["HOST"],
    "GROQ_CHAT_MODEL": ["GROQ_CHAT_MODEL", "CHAT_MODEL"],
    "GROQ_REALTIME_MODEL": ["GROQ_REALTIME_MODEL", "REALTIME_MODEL"],
    "OWNER_EMAIL": ["OWNER_EMAIL"],
    "OWNER_USERNAME": ["OWNER_USERNAME"],
}


def get_env(key, default=None, *, allow_legacy=True):
    if not key:
        return default
    for candidate in [key] + (STANDARDIZED_KEYS.get(key, []) if allow_legacy else []):
        value = os.getenv(candidate)
        if value is not None and str(value).strip() != "":
            return value.strip()
    return default


def set_env(key, value):
    if not key:
        return False
    os.environ[key] = str(value).strip()
    return True


def mask_secret(value):
    if value is None:
        return ""
    value = str(value).strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + ("*" * max(4, len(value) - 8)) + value[-4:]


def maybe_upload_to_supabase(file_path, bucket_name="artifacts"):
    """Upload generated application artifacts to Supabase Storage when configured."""
    if not file_path:
        return None
    try:
        from Backend.Database.supabase_client import supabase
        if not supabase:
            return None
        path = Path(file_path)
        if not path.exists():
            return None
        with path.open("rb") as fh:
            storage = supabase.storage.from_(bucket_name)
            storage.upload(path.name, fh, file_options={"content-type": "application/octet-stream"})
        return f"{bucket_name}/{path.name}"
    except Exception:
        return None

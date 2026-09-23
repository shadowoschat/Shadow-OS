import asyncio
import logging
import os
import re
import threading
import time
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

from dotenv import load_dotenv
import edge_tts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TTS_DIR = Path(__file__).resolve().parent.parent / "Data" / "TTS"
TTS_DIR.mkdir(parents=True, exist_ok=True)

VOICE_MAP = {
    "en": {"male": "en-IN-PrabhatNeural", "female": "en-IN-NeerjaNeural"},
    "hi": {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"},
    "mr": {"male": "mr-IN-ManoharNeural", "female": "mr-IN-AarohiNeural"},
}
VALID_VOICES = {voice for voices in VOICE_MAP.values() for voice in voices.values()}
EXPRESSION_TAGS = {
    "[laughter]": "<break time='700ms'/>",
    "[laughs]": "<break time='700ms'/>",
    "[sigh]": "<break time='600ms'/>",
    "[gasp]": "<break time='500ms'/>",
    "[clears throat]": "<break time='800ms'/>",
}
EXPRESSION_PATTERN = re.compile(r"\[(laughter|laughs|sigh|gasp|clears throat)\]", re.IGNORECASE)

speaking_thread = None
stop_event = threading.Event()
speech_status = "idle"

load_dotenv()


def get_speech_status():
    """Returns the current status of speech."""
    global speech_status
    return speech_status


def normalize_language(language):
    if not language:
        return "en"
    value = str(language).strip().lower()
    aliases = {
        "english": "en",
        "en": "en",
        "en-in": "en",
        "hindi": "hi",
        "hi": "hi",
        "mr": "mr",
        "marathi": "mr",
    }
    for alias, normalized in aliases.items():
        if value == alias or value.startswith(alias):
            return normalized
    if "hi" in value:
        return "hi"
    if "mr" in value or "marathi" in value:
        return "mr"
    if "en" in value:
        return "en"
    return "en"


def normalize_voice_name(voice_name):
    if not voice_name:
        return None
    candidate = str(voice_name).strip()
    lowered = candidate.lower()
    for actual in VALID_VOICES:
        if actual.lower() == lowered:
            return actual
    if "prabhat" in lowered:
        return "en-IN-PrabhatNeural"
    if "neerja" in lowered:
        return "en-IN-NeerjaNeural"
    if "madhur" in lowered:
        return "hi-IN-MadhurNeural"
    if "swara" in lowered:
        return "hi-IN-SwaraNeural"
    if "manohar" in lowered:
        return "mr-IN-ManoharNeural"
    if "arohi" in lowered:
        return "mr-IN-AarohiNeural"
    return None


def resolve_voice(language=None, gender=None, voice_name=None):
    selected_voice = normalize_voice_name(voice_name)
    if selected_voice:
        return selected_voice

    resolved_language = normalize_language(language or os.getenv("InputLanguage") or os.getenv("INPUT_LANGUAGE"))
    default_voices = VOICE_MAP.get(resolved_language, VOICE_MAP["en"])
    if gender and str(gender).lower().startswith("m"):
        return default_voices["male"]
    return default_voices["female"]


def get_voice_settings():
    load_dotenv()
    language = os.getenv("InputLanguage") or os.getenv("INPUT_LANGUAGE") or "en"
    voice_name = os.getenv("ASSISTANT_VOICE") or os.getenv("AssistantVoice") or resolve_voice(language)
    resolved_voice = resolve_voice(language=language, voice_name=voice_name)
    gender = "male" if any(resolved_voice.lower().endswith(name.lower()) for name in ["PrabhatNeural", "MadhurNeural", "ManoharNeural"]) else "female"
    return {
        "language": normalize_language(language),
        "voice": resolved_voice,
        "gender": gender,
        "available_voices": {
            "en": {"male": VOICE_MAP["en"]["male"], "female": VOICE_MAP["en"]["female"]},
            "hi": {"male": VOICE_MAP["hi"]["male"], "female": VOICE_MAP["hi"]["female"]},
            "mr": {"male": VOICE_MAP["mr"]["male"], "female": VOICE_MAP["mr"]["female"]},
        },
    }


def _build_ssml(text, voice_name, language):
    safe_text = str(text or "").strip()
    if not safe_text:
        raise ValueError("TTS text is empty.")

    parts = []
    for chunk in re.split(r"(\[[^\]]+\])", safe_text):
        if not chunk:
            continue
        match = EXPRESSION_PATTERN.fullmatch(chunk.strip())
        if match:
            tags = f"[{match.group(1).lower()}]"
            parts.append(EXPRESSION_TAGS.get(tags, "<break time='500ms'/>"))
            continue
        cleaned = " ".join(chunk.strip().split())
        if cleaned:
            parts.append(escape(cleaned))

    spoken_text = " ".join(part for part in parts if part)
    if not spoken_text:
        raise ValueError("TTS text is empty after striping expression tags.")

    return (
        f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
        f"xml:lang='{language}'><voice name='{voice_name}'>{spoken_text}</voice></speak>"
    )


async def _generate_audio_file(text, voice_name, language, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ssml = _build_ssml(text, voice_name, language)
    communicate = edge_tts.Communicate(ssml, voice=voice_name)
    await communicate.save(str(output_path))
    return output_path


def generate_audio_file(text, voice=None, language=None, gender=None, output_name=None):
    clean_text = str(text or "").strip()
    if not clean_text:
        raise ValueError("TTS text is empty.")

    resolved_language = normalize_language(language or os.getenv("InputLanguage") or os.getenv("INPUT_LANGUAGE"))
    resolved_voice = resolve_voice(language=resolved_language, gender=gender, voice_name=voice)
    requested_name = (output_name or "voice.mp3").strip() or "voice.mp3"
    if not requested_name.lower().endswith(".mp3"):
        requested_name = f"{requested_name}.mp3"

    output_path = TTS_DIR / requested_name
    temp_path = output_path.with_name(f".{output_path.name}.tmp")

    if temp_path.exists():
        try:
            temp_path.unlink()
        except OSError:
            pass

    logger.info("TTS generation started | voice=%s | language=%s | chars=%s | target=%s", resolved_voice, resolved_language, len(clean_text), output_path.name)
    try:
        try:
            asyncio.run(_generate_audio_file(clean_text, resolved_voice, resolved_language, temp_path))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_generate_audio_file(clean_text, resolved_voice, resolved_language, temp_path))
            finally:
                loop.close()

        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise FileNotFoundError(f"Generated TTS temp file is missing or empty: {temp_path}")

        os.replace(temp_path, output_path)
    except Exception as exc:
        logger.exception("TTS generation failed | voice=%s | file=%s | error=%s", resolved_voice, output_path.name, exc)
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise FileNotFoundError(f"Generated TTS file is missing or empty: {output_path}")

    logger.info("TTS generation completed | file=%s | size=%s bytes", output_path.name, output_path.stat().st_size)
    return str(output_path)


def _play_audio_file(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        import pygame
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        pygame.mixer.music.stop()
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as exc:
        logger.warning("pygame playback failed for %s: %s", path, exc)
        try:
            os.startfile(str(path))
        except Exception as e:
            logger.error("Fallback playback also failed: %s", e)
            raise


def Speak(text: str, voice: str = None, language: str = None, gender: str = None) -> bool:
    """Generate and play assistant speech asynchronously using Edge TTS."""
    global speaking_thread, stop_event, speech_status

    clean_text = str(text or "").strip()
    if not clean_text:
        logger.warning("Refusing to speak empty text.")
        return False

    stop_event.set()
    stop_event.clear()
    speech_status = "speaking"

    def _speak_worker():
        global speech_status
        try:
            resolved_language = normalize_language(language or os.getenv("InputLanguage") or os.getenv("INPUT_LANGUAGE"))
            resolved_voice = resolve_voice(language=resolved_language, gender=gender, voice_name=voice)
            target_path = TTS_DIR / f"{uuid.uuid4().hex}.mp3"
            asyncio.run(_generate_audio_file(clean_text, resolved_voice, resolved_language, target_path))
            _play_audio_file(target_path)
            logger.info("Finished speaking Edge TTS audio")
        except Exception as exc:
            logger.exception("Edge TTS generation/playback error: %s", exc)
        finally:
            speech_status = "idle"

    speaking_thread = threading.Thread(target=_speak_worker, daemon=True)
    speaking_thread.start()
    return True


def Stop():
    """Immediately stop current speech."""
    global speech_status
    try:
        import pygame
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
    except Exception:
        pass
    speech_status = "idle"
    logger.info("Speech stop signal sent.")


def TextToSpeech(text, func=None, voice=None, language=None, gender=None):
    """Backward-compatible wrapper for existing Flask code and legacy callers."""
    text = str(text or "").strip()
    if not text:
        return False
    result = Speak(text, voice=voice, language=language, gender=gender)
    if callable(func):
        try:
            func()
        except Exception as exc:
            logger.warning("Optional TTS callback failed: %s", exc)
    return result


if __name__ == "__main__":
    test_text = "Hello, I am Astra. [laughter] I am ready to help you."
    Speak(test_text)
    while speech_status != "idle":
        time.sleep(0.1)

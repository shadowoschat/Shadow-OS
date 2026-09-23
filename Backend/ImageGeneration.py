import os
import random
import urllib.parse
from datetime import datetime
from io import BytesIO
from pathlib import Path
from time import sleep

import requests
from PIL import Image, ImageDraw

from Backend.config import get_env

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
FILES_DIR = DATA_DIR / "Files"
IMAGE_DIR = DATA_DIR / "Generate_ai_images"
IMAGE_STATUS_FILE = FILES_DIR / "imageGeneration.data"

DATA_DIR.mkdir(exist_ok=True)
FILES_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)

IMAGE_WIDTH = int(get_env("IMAGE_WIDTH", "512"))
IMAGE_HEIGHT = int(get_env("IMAGE_HEIGHT", "512"))
IMAGE_COUNT = max(1, min(5, int(get_env("IMAGE_COUNT", "2"))))
IMAGE_TIMEOUT = int(get_env("IMAGE_TIMEOUT", "60"))
DEFAULT_PROMPT = get_env("DEFAULT_IMAGE_PROMPT", "A realistic futuristic sports car in neon city")
ENHANCEMENT = ", ultra realistic, 4k, cinematic lighting, highly detailed"


def _ensure_status_file():
    if not IMAGE_STATUS_FILE.exists():
        IMAGE_STATUS_FILE.write_text("false,false", encoding="utf-8")


def is_valid_image(response):
    content_type = response.headers.get("content-type", "").lower()
    if "image" not in content_type:
        return False
    try:
        with Image.open(BytesIO(response.content)) as img:
            img.verify()
        return True
    except Exception:
        return False


def generate_single_image(prompt, image_num):
    enhanced_prompt = (prompt + ENHANCEMENT)[:200].strip()
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote_plus(enhanced_prompt)}"
    url += f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&nologo=true&seed={seed}"

    for attempt in range(3):
        try:
            response = requests.get(url, timeout=IMAGE_TIMEOUT)
            if response.status_code != 200:
                response.raise_for_status()
            if not is_valid_image(response):
                raise ValueError("Invalid image received from Pollinations AI")
            with Image.open(BytesIO(response.content)) as img:
                return img.convert("RGB")
        except Exception:
            if attempt < 2:
                sleep(2 ** attempt)
                continue
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"API Fail: {prompt[:40]}...", fill="white")
    return img.convert("RGB")


def generate_images(prompt):
    _ensure_status_file()
    safe_name = ''.join(c for c in prompt if c.isalnum() or c in ' -_').strip().replace(' ', '_').lower()[:50]
    safe_name = safe_name or "image"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_paths = []

    for i in range(1, IMAGE_COUNT + 1):
        img = generate_single_image(prompt, i)
        if img:
            filename = f"{safe_name}_{timestamp}_{i:02d}.png"
            file_path = IMAGE_DIR / filename
            img.save(file_path, "PNG")
            saved_paths.append(str(file_path))
        sleep(1)

    return saved_paths


def read_status_file():
    _ensure_status_file()
    try:
        data = IMAGE_STATUS_FILE.read_text(encoding="utf-8").strip().lower()
        parts = [x.strip() for x in data.split(",")]
        if len(parts) != 2:
            return False, False
        return parts[0] == "true", parts[1] == "true"
    except Exception:
        return False, False


def write_status_file(generate_flag=False, open_flag=False):
    _ensure_status_file()
    IMAGE_STATUS_FILE.write_text(f"{str(generate_flag).lower()},{str(open_flag).lower()}", encoding="utf-8")


if __name__ == "__main__":
    _ensure_status_file()
    print("Monitoring image generation status file at:", IMAGE_STATUS_FILE)
    while True:
        try:
            generate_flag, _ = read_status_file()
            if generate_flag:
                write_status_file(False, False)
                images = generate_images(DEFAULT_PROMPT)
                if images:
                    print("Images generated:", images)
        except KeyboardInterrupt:
            break
        except Exception:
            pass
        sleep(2)

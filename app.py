import os
import re
import socket
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
from dotenv import load_dotenv
load_dotenv(ENV_PATH, override=False)

import requests
import psutil
from Backend.config import get_env, mask_secret
from Backend.Automation import Automation, SetVolume, SetBrightness, TakeScreenshot, StartScreenRecording, StopScreenRecording
from Backend.RealtimeSearchEngine import RealtimeSearchEngine as realtime_search
from Backend.Model import FirstLayerDMM
from Backend.AuthDB import create_user as db_create_user, verify_user as db_verify_user, verify_user_exists, update_user_password, get_user_by_email, mark_user_verified
from Backend.Chatbot import ChatBot
from Backend.SketchAnimator import draw_sketch, get_image_path
import datetime  # For chat history dates
from Backend.TextToSpeech import TextToSpeech, generate_audio_file, get_voice_settings, resolve_voice
import time
import threading
import multiprocessing
import asyncio
import subprocess
import logging
import platform
import secrets
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import safe_join
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort, send_file
from flask_cors import CORS
from flask import send_from_directory

# tasks = FirstLayerDMM(user_msg)
CURRENT_SKETCH_SUBJECT = None

# MEMORY FILE PATH (cross-platform)
DATA_DIR = Path(__file__).parent / "Data"
DATA_DIR.mkdir(exist_ok=True)
TTS_AUDIO_FILE = DATA_DIR / "TTS" / "voice.mp3"

# Compatibility: legacy append-only backup file (newline-delimited JSON).
# Newer deployments use PostgreSQL chat_history; keep a file path for
# read-only compatibility with older endpoints.

# Wake word
WAKE_WORD = "Astra"


from Backend.Database.chat_db import get_chat_history, save_chat_message, get_chat_history_for_display
from Backend.Database.memory_db import get_user_memory, save_interaction, save_short_term_memory
from Backend.Database.admin_db import (get_dashboard_stats, get_all_users, get_recent_logins,
    get_recent_admin_events, record_login_event, record_system_event,
    load_devices_db, save_device_db, is_device_authorized_db,
    update_user_by_admin, delete_user_by_admin)
from Backend.AuthDB import ensure_owner_account
from Backend.Database.connection import get_db_cursor, database_is_available

# -----------------------------
# ENV & PATH SETUP
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "Backend")

FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "Templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "Static")

# Explicit absolute path for .env
load_dotenv(os.path.join(BASE_DIR, ".env"))

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static",
)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY is required. Set it in the Render environment variables before starting the app.")
app.secret_key = secret_key

# Only attempt to ensure the owner account if a DATABASE_URL is configured.
# This avoids noisy warnings for development runs that don't have a database.
db_url = os.getenv("DATABASE_URL")
owner_email = get_env("OWNER_EMAIL")
owner_username = get_env("OWNER_USERNAME")
owner_password = get_env("OWNER_PASSWORD")
if not db_url:
    app.logger.info("Skipping ensure_owner_account: DATABASE_URL not set.")
elif owner_email and owner_username and owner_password:
    try:
        ensure_owner_account(
            first_name="Admin",
            last_name="User",
            email=owner_email,
            username=owner_username,
            password=owner_password,
        )
        app.logger.info("Owner/admin account ensured from environment configuration.")
    except Exception as exc:
        app.logger.warning("Failed to ensure default owner account: %s", exc)
else:
    app.logger.info("Skipping ensure_owner_account: OWNER_EMAIL/OWNER_USERNAME/OWNER_PASSWORD not set.")

def _get_cors_origins():
    configured = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


CORS(app, resources={r"/api/*": {"origins": _get_cors_origins()}})

# -----------------------------
# Email Configuration
# -----------------------------
def send_email_otp(to_email, otp):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")

    if not all([smtp_host, smtp_username, smtp_password, smtp_from]):
        app.logger.error("SMTP configuration is missing. Cannot send OTP.")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = to_email
    msg['Subject'] = 'Your OTP Code - Shadow OS'

    body = f"Your OTP code is: {otp}\n\nThis code will expire in 5 minutes."
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Prefer explicit SSL if configured or if common SSL port used
        if use_ssl or smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        # Provide explicit auth failure logging (SMTP code + message)
        smtp_code = getattr(e, 'smtp_code', None)
        smtp_error = getattr(e, 'smtp_error', None)
        app.logger.error("SMTP auth failed: %s %s", smtp_code, smtp_error)
        return False
    except Exception:
        app.logger.exception("Failed to send email")
        return False

app.logger.setLevel(logging.WARNING)

# Suppress Flask/Werkzeug access logs
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

# -----------------------------
# DEVICE MANAGEMENT (PostgreSQL)
# -----------------------------
def load_devices():
    return load_devices_db()

def save_devices(devices):
    pass  # Devices are saved individually via save_device_db

def is_device_authorized():
    device_name = platform.node()
    return is_device_authorized_db(device_name)

def authorize_device():
    device_name = platform.node()
    user_id = None
    try:
        from flask import session as flask_session
        user_id = flask_session.get('user_id')
    except Exception:
        pass
    if user_id:
        save_device_db(user_id, device_name)

# -----------------------------
# LOGIN REQUIRED DECORATOR
# -----------------------------
# -----------------------------
# SYSTEM DATA (for /system-data)
# -----------------------------
system_data = {
    "cpu": 0,
    "memory": {"used": 0, "total": 0, "percent": 0},
    "storage": {"used": 0, "total": 0, "percent": 0},
    "battery": {"percent": 100, "charging": False},
}


def update_system_data():
    """Background thread to update system_data safely."""
    if not psutil:
        app.logger.warning(
            "psutil not available; /system-data will return zeros.")
        return

    # Prime cpu_percent() so next calls are meaningful
    try:
        psutil.cpu_percent(interval=None)
    except Exception:
        pass

    while True:
        try:
            system_data["cpu"] = psutil.cpu_percent(interval=0.5)

            mem = psutil.virtual_memory()
            system_data["memory"] = {
                "used": round(mem.used / (520**3), 1),
                "total": round(mem.total / (520**3), 1),
                "percent": float(mem.percent),
            }

            disk = psutil.disk_usage("/")
            system_data["storage"] = {
                "used": round(disk.used / (520**3), 1),
                "total": round(disk.total / (520**3), 1),
                "percent": round((disk.used / disk.total) * 100, 1) if disk.total else 0,
            }

            # sensors_battery() can be None on desktops
            batt = None
            try:
                batt = psutil.sensors_battery()
            except Exception:
                batt = None

            if batt:
                system_data["battery"] = {
                    "percent": float(batt.percent),
                    "charging": bool(batt.power_plugged),
                }
        except Exception as e:
            app.logger.exception("System Monitor Error: %s", e)

        time.sleep(2)


SYSTEM_MONITOR_THREAD = None


def start_system_monitor():
    global SYSTEM_MONITOR_THREAD
    if SYSTEM_MONITOR_THREAD is not None and SYSTEM_MONITOR_THREAD.is_alive():
        return SYSTEM_MONITOR_THREAD
    SYSTEM_MONITOR_THREAD = threading.Thread(
        target=update_system_data,
        daemon=True,
        name="system-monitor",
    )
    SYSTEM_MONITOR_THREAD.start()
    return SYSTEM_MONITOR_THREAD


start_system_monitor()

# -----------------------------
# SIMPLE SERVER-SIDE COOLDOWN (helps reduce 429)
# -----------------------------
CHAT_MIN_INTERVAL_SEC = float(os.getenv("CHAT_MIN_INTERVAL_SEC", "0.3"))
_last_chat_ts = 0.0
_chat_lock = threading.Lock()


def _check_server_cooldown():
    global _last_chat_ts
    with _chat_lock:
        now = time.time()
        diff = now - _last_chat_ts
        if diff < CHAT_MIN_INTERVAL_SEC:
            return CHAT_MIN_INTERVAL_SEC - diff
        _last_chat_ts = now
        return 0.0


def _looks_like_429(err: Exception) -> bool:
    s = str(err).lower()
    return ("429" in s) or ("rate limit" in s) or ("too many requests" in s)


def _call_with_backoff(fn, arg: str, max_retries: int = 2):
    """
    Retry on 429-like errors with exponential backoff.
    """
    delay = 1.0
    for attempt in range(max_retries + 1):
        try:
            return fn(arg)
        except Exception as e:
            if _looks_like_429(e) and attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def save_interaction_wrapper(user_id, user_msg, task_type, response):
    try:
        if user_id:
            save_interaction(user_id, {
                "timestamp": time.time(),
                "user_msg": user_msg,
                "task_type": task_type,
                "response": response
            })
    except Exception as e:
        app.logger.error(f"Error saving interaction: {e}")

def append_to_backup_wrapper(user_id, user_msg, final_response):
    """Backup is now handled by saving to chat_history in PostgreSQL."""
    try:
        if user_id:
            save_chat_message(user_id, "user", str(user_msg))
            save_chat_message(user_id, "assistant", str(final_response))
    except Exception as e:
        app.logger.error(f"Backup save error: {e}")

def save_chat_to_log(user_id, user_msg=None, final_response=None):
    """Save chat pair to PostgreSQL chat_history table.

    Supports both call styles:
    save_chat_to_log(user_id, user_msg, final_response)
    save_chat_to_log(user_msg, final_response)
    """
    if final_response is None:
        final_response = user_msg
        user_msg = user_id
        user_id = session.get('user_id')

    try:
        if user_id:
            save_chat_message(user_id, "user", str(user_msg))
            save_chat_message(user_id, "assistant", str(final_response))
    except Exception as e:
        app.logger.error(f"ChatLog save error: {e}")


def append_to_backup(user_msg, final_response, user_id=None):
    """Compatibility wrapper for permanent chat backup. Uses active session user if omitted."""
    if user_id is None:
        user_id = session.get('user_id')
    try:
        if user_id:
            save_chat_message(user_id, "user", str(user_msg))
            save_chat_message(user_id, "assistant", str(final_response))
    except Exception as e:
        app.logger.error(f"Backup save error: {e}")


def _run_automation(commands):
    """
    Automation is async in your Backend/Automation.py,
    so run it inside a thread with its own asyncio.run().
    """
    try:
        asyncio.run(Automation(commands))
    except Exception as e:
        app.logger.exception("Automation error: %s", e)


# -----------------------------
# AUTHENTICATION ROUTES
# -----------------------------
def role_is_admin(role_value):
    return str(role_value or '').strip().lower() in {'admin', 'owner'}


@app.route("/")
def index():
    # Always show loading page first if no user session
    if 'user' not in session:
        return render_template("loading.html")
    return redirect('/admin' if is_admin_session() else '/dashboard')


@app.route("/loading")
def loading():
    return render_template("loading.html")


@app.route("/login")
def login_page():
    if 'user' in session:
        return redirect('/admin' if is_admin_session() else '/dashboard')
    return render_template("login.html")


@app.route("/signup")
def signup_page():
    if 'user' in session:
        return redirect('/admin' if is_admin_session() else '/dashboard')
    return render_template("signup.html")


@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot-password.html")


@app.route("/otp")
def otp_page():
    # PROTECT: Must have pending_otp session from login attempt
    if 'pending_otp' not in session:
        return redirect('/login')
    # OTP timeout: 5 minutes
    if 'otp_time' not in session:
        session['otp_time'] = time.time()
    elif time.time() - session['otp_time'] > 300:  # 5min
        session.clear()
        return redirect('/login')
    return render_template("otp.html")


@app.route("/index")
def main_app():
    if 'user' not in session:
        return redirect('/login')
    return redirect('/admin' if is_admin_session() else '/dashboard')



from Backend.Database.supabase_client import supabase

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    identifier = (data.get('username') or '').strip()
    password = data.get('password')

    if not identifier or not password:
        return jsonify({'success': False, 'message': 'Missing credentials'}), 400

    # Fallback to look up email if identifier is username
    email_for_login = identifier
    if '@' not in identifier:
        from Backend.AuthDB import get_user_by_id
        with get_db_cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE lower(username) = %s", (identifier.lower(),))
            row = cursor.fetchone()
            if row:
                email_for_login = row[0]
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    try:
        if not supabase:
            raise Exception("Supabase client not configured")
        # Sign in with Supabase
        auth_res = supabase.auth.sign_in_with_password({"email": email_for_login, "password": password})
        if not auth_res.user:
            raise Exception("Login failed")
        
        # Verify user in our DB
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "SELECT id, username, role, is_verified FROM users WHERE id = %s",
                (str(auth_res.user.id),)
            )
            row = cursor.fetchone()
            if not row:
                raise Exception("User record not found in public.users")
            
            user_id = str(row[0])
            username = row[1]
            role = row[2]
            
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
        
        session['user'] = username
        session['user_id'] = user_id
        session['role'] = str(role or '').strip().lower()
        session['access_token'] = auth_res.session.access_token
        
        record_login_event(user_id, success=True, details='User login via Supabase', ip_address=request.remote_addr)
        return jsonify({'success': True, 'redirect': '/admin' if role_is_admin(role) else '/dashboard'})
    except Exception as e:
        record_login_event(identifier, success=False, details=str(e), ip_address=request.remote_addr)
        return jsonify({'success': False, 'message': 'Invalid credentials or unverified email.'}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    try:
        if supabase and 'access_token' in session:
            # We would theoretically sign out from supabase here, but session clear is enough for local
            pass
    except:
        pass
    session.clear()
    return jsonify({'success': True, 'redirect': '/login'})


def is_admin_session():
    if role_is_admin(session.get('role')):
        return True

    user_id = session.get('user_id')
    if not user_id:
        return False

    try:
        from Backend.AuthDB import get_user_by_id
        user = get_user_by_id(user_id)
        if not user:
            return False
        return role_is_admin(user.get('role'))
    except Exception as exc:
        app.logger.warning('Admin session check failed for %s: %s', user_id, exc)
        return False


@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json() or {}
    first = (data.get('first') or '').strip()
    last = (data.get('last') or '').strip()
    email = (data.get('email') or '').strip()
    username = (data.get('username') or '').strip()
    password = data.get('password')

    if not all([first, last, email, username, password]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    try:
        if not supabase:
            raise Exception("Supabase client not configured")
            
        # Check if username exists in local DB first to avoid confusing auth states
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE lower(username) = %s OR lower(email) = %s", (username.lower(), email.lower()))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Username or Email already exists'}), 409

        # Sign up in Supabase
        auth_res = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {
                    "first_name": first,
                    "last_name": last,
                    "username": username
                }
            }
        })
        
        user = auth_res.user
        if not user:
            raise Exception("Supabase signup returned no user object")
            
        # Insert into local public.users
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO users (id, first_name, last_name, email, username, role, is_verified, status)
                VALUES (%s, %s, %s, %s, %s, 'user', FALSE, 'active')
                ON CONFLICT (id) DO NOTHING
                """,
                (str(user.id), first, last, email, username)
            )
        session['role'] = 'user'

        # Instead of our custom OTP, rely on Supabase's email confirmation.
        return jsonify({'success': True, 'redirect': '/login', 'message': 'Registration successful! Please check your email to verify your account.'})
    except Exception as e:
        app.logger.error(f"Signup error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# Forgot password endpoint consolidated later in this file to support
# either Supabase password-reset emails or the local OTP flow.


# Removing old verify and clear_otp routes since Supabase handles email verification
@app.route("/api/verify", methods=["POST"])
def api_verify():
    return jsonify({'success': False, 'message': 'Use email link to verify.'}), 400

@app.route("/api/clear-otp", methods=["POST"])
def clear_otp():
    return jsonify({'success': True})



# -----------------------------
# NEW FRONTEND WORKSTATION ROUTES
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template("dashboard.html")


@app.route("/data")
def data_page():
    if 'user' not in session:
        return redirect('/login')
    if not is_admin_session():
        abort(403)
    return render_template("data.html")


@app.route("/admin")
def admin_page():
    if 'user' not in session:
        return redirect('/login')
    if not is_admin_session():
        abort(403)
    return render_template("admin.html")


@app.route("/ai-chatbot")
def ai_chatbot():
    if 'user' not in session:
        return redirect('/login')
    return render_template("ai-chatbot.html")


@app.route("/image")
def image_studio():
    if 'user' not in session:
        return redirect('/login')
    return render_template("image.html")


@app.route("/sketch")
def sketch_studio():
    if 'user' not in session:
        return redirect('/login')
    return render_template("sketch.html")


@app.route("/music")
def music_player():
    if 'user' not in session:
        return redirect('/login')
    return render_template("music.html")


@app.route("/files")
def files_explorer():
    if 'user' not in session:
        return redirect('/login')
    return render_template("files.html")


@app.route("/api-keys")
def api_keys_page():
    if 'user' not in session:
        return redirect('/login')
    return render_template("api-keys.html")


@app.route("/upgrade")
def upgrade_page():
    if 'user' not in session:
        return redirect('/login')
    return render_template("upgrade.html")


@app.route("/profile")
def profile_page():
    if 'user' not in session:
        return redirect('/login')
    return render_template("profile.html")


# -----------------------------
# EXISTING PAGE ROUTES (BACKWARD COMPAT)
# -----------------------------
@app.route("/app")
def app_index():
    if 'user' not in session:
        return redirect('/login')
    return redirect('/admin' if is_admin_session() else '/dashboard')


@app.route("/chatbot")
def chatbot():
    if 'user' not in session:
        return redirect('/login')
    return redirect('/ai-chatbot')


@app.route("/history")
def history_page():
    if 'user' not in session:
        return redirect('/login')
    return redirect('/ai-chatbot')


# -----------------------------
# API : SYSTEM STATUS (UNCHANGED)
# -----------------------------
@app.route("/api/system-stats")
def system_api():
    return jsonify(system_data)

@app.route("/api/session-status")
def session_status():
    logged_in = bool(session.get('user'))
    username = session.get('user', '') if logged_in else ''
    email = ''
    first = ''
    last = ''
    is_admin = is_admin_session()
    role = 'ADMIN' if is_admin else 'USER'
    if logged_in:
        username = str(username)
        try:
            # Prefer authoritative data from PostgreSQL
            try:
                from Backend.AuthDB import get_user_by_id
                user_id = session.get('user_id')
                if user_id:
                    u = get_user_by_id(user_id)
                    if u:
                        email = u.get('email', '')
                        first = u.get('first_name') or u.get('first') or ''
                        last = u.get('last_name') or u.get('last') or ''
                        username = u.get('username', username)
                        if u.get('role') == 'admin':
                            is_admin = True
                            role = 'ADMIN'
            except Exception:
                # Fallback: leave values blank but do not crash
                pass
        except Exception as e:
            app.logger.error(f"Error fetching user details: {e}")
    return jsonify({
        'logged_in': logged_in,
        'username': username,
        'email': email or (f"{username}@shadow.os" if username else ""),
        'first': first,
        'last': last,
        'role': role,
        'is_admin': is_admin,
    })

@app.route("/status")
def status():
    return {"status": "online"}


# -----------------------------
# HELPER DATA APIs (NEW)
# -----------------------------
@app.route("/api/songs")
def api_songs():
    """List all .mp3/.wav files from Data/Songs/"""
    songs = []

    # 1) Files from Data/Songs (user-uploaded)
    songs_dir = DATA_DIR / "Songs"
    songs_dir.mkdir(exist_ok=True)
    if songs_dir.exists():
        for f in sorted(songs_dir.iterdir()):
            if f.suffix.lower() in ('.mp3', '.wav', '.ogg', '.flac') and f.is_file():
                songs.append({
                    "name": f.name,
                    "url": f"/data/Songs/{f.name}"
                })

    # 2) Built-in frontend assets under Frontend/Music
    frontend_music_dir = Path(TEMPLATES_DIR).parent / "Music"
    if frontend_music_dir.exists():
        for f in sorted(frontend_music_dir.iterdir()):
            if f.suffix.lower() in ('.mp3', '.wav', '.ogg', '.flac') and f.is_file():
                # Avoid duplicate names (Data wins if duplicated)
                if not any(s['name'] == f.name for s in songs):
                    songs.append({
                        "name": f.name,
                        "url": f"/music/{f.name}"
                    })

    return jsonify(songs)


@app.route("/api/images")
def api_images():
    """List all .png/.jpg files from Data/Generate_ai_images/"""
    img_dir = DATA_DIR / "Generate_ai_images"
    img_dir.mkdir(exist_ok=True)
    images = []
    for f in sorted(img_dir.iterdir(), reverse=True):
        if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp') and f.is_file():
            images.append({
                "name": f.name,
                "url": f"/data/Generate_ai_images/{f.name}"
            })
    return jsonify(images)


@app.route("/api/files-list")
def api_files_list():
    """List all files in Data/ directory recursively (top 2 levels)"""
    files = []
    for f in DATA_DIR.rglob("*"):
        if f.is_file():
            try:
                size_bytes = f.stat().st_size
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1048576:
                    size_str = f"{size_bytes // 1024} KB"
                else:
                    size_str = f"{size_bytes // 1048576} MB"
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(DATA_DIR)),
                    "size": size_str
                })
            except Exception:
                pass
    return jsonify(files)


@app.route("/api/data-overview")
def api_data_overview():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if not is_admin_session():
        return jsonify({"error": "Forbidden"}), 403

    # Chat entries from PostgreSQL (admin sees all recent chats as overview)
    chat_entries = []
    try:
        from Backend.Database.connection import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT c.created_at, u.username, c.role, c.message
                FROM chat_history c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.role = 'user'
                ORDER BY c.created_at DESC LIMIT 20
                """
            )
            for row in cursor.fetchall():
                chat_entries.append({
                    'timestamp': row[0].isoformat() + 'Z' if row[0] else '',
                    'user': row[1] or 'unknown',
                    'action': row[3][:100] if row[3] else '',
                    'status': 'OK',
                    'details': '',
                })
    except Exception:
        chat_entries = []

    # Device entries from PostgreSQL
    device_entries = []
    try:
        devices = load_devices_db()
        for device in devices:
            device_entries.append({
                'timestamp': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                'user': session.get('user', 'operator'),
                'action': 'Device authorized',
                'status': 'ACTIVE',
                'details': str(device),
            })
    except Exception:
        device_entries = []

    # User entries from PostgreSQL
    user_entries = []
    try:
        all_users = get_all_users()
        for u in all_users:
            user_entries.append({
                'timestamp': u.get('created_at', ''),
                'user': u.get('username', 'unknown'),
                'action': 'Account registered',
                'status': u.get('status', 'active').upper(),
                'details': u.get('email', ''),
            })
    except Exception:
        user_entries = []

    # Login entries from PostgreSQL
    login_entries = []
    try:
        logins = get_recent_logins(20)
        for item in logins:
            login_entries.append({
                'timestamp': item.get('timestamp', ''),
                'user': item.get('user', 'unknown'),
                'action': 'Login attempt',
                'status': 'SUCCESS' if item.get('success') else 'FAILED',
                'details': item.get('details', ''),
            })
    except Exception:
        login_entries = []

    # System events from PostgreSQL
    system_events = []
    try:
        events = get_recent_admin_events(20)
        for item in events:
            system_events.append({
                'timestamp': item.get('timestamp', ''),
                'user': item.get('user', 'system'),
                'action': item.get('action', 'Event'),
                'status': item.get('status', 'INFO'),
                'details': item.get('details', ''),
            })
    except Exception:
        system_events = []

    return jsonify({
        'chat_log': chat_entries[:20],
        'device_history': device_entries,
        'user_login_history': login_entries,
        'user_activity': user_entries,
        'system_logs': system_events,
    })


@app.route("/api/admin/overview")
def api_admin_overview():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if not is_admin_session():
        return jsonify({'error': 'Forbidden'}), 403

    users = get_all_users()
    for u in users:
        u['name'] = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or 'Unknown'
        u['password_status'] = 'Configured'
        u['login_count'] = 0
        u['created_date'] = u.get('created_at', 'N/A')
        u['current_session'] = 'N/A'

    logins = get_recent_logins(40)
    for l in logins:
        l['login_time'] = l.get('timestamp')
        l['logout_time'] = ''
        l['session_status'] = 'SUCCESS' if l.get('success') else 'FAILED'
        l['result'] = 'SUCCESS' if l.get('success') else 'FAILED'
        l['ip'] = l.get('ip_address')
        l['device'] = l.get('user_agent', 'unknown')[:60]

    events = get_recent_admin_events(30)
    warnings = []
    for e in events:
        warnings.append({
            'timestamp': e.get('timestamp'),
            'severity': e.get('status', 'INFO'),
            'title': e.get('action'),
            'message': e.get('details')
        })

    connections = []
    info = {
        'os': platform.system(),
        'python_version': platform.python_version(),
        'flask_status': 'Running',
        'cpu': f"{platform.processor() or 'Unknown'}",
        'server_status': 'Online',
        'current_user': session.get('user', 'admin'),
        'process_status': 'Nominal',
    }

    return jsonify({
        'users': users,
        'login_history': logins,
        'problems': warnings,
        'ports': connections,
        'system': info,
    })

@app.route("/api/admin/terminal", methods=['POST'])
def api_admin_terminal():
    if 'user' not in session or not is_admin_session():
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json(silent=True) or {}
    command = str(data.get('command') or '').strip()
    if not command:
        return jsonify({'ok': False, 'output': 'No command entered.'}), 400

    safe_commands = {
        'whoami': ['whoami'],
        'pwd': ['pwd'],
        'hostname': ['hostname'],
        'python --version': ['python', '--version'],
        'python3 --version': ['python3', '--version'],
        'ls': ['ls'],
        'dir': ['dir'],
        'echo': ['echo'],
    }
    normalized = command.lower()
    allowed = False
    exec_args = None
    for label, args in safe_commands.items():
        if normalized == label or normalized.startswith(f"{label} "):
            allowed = True
            exec_args = args + ([] if label not in ('echo',) else [command.split(' ', 1)[1] if ' ' in command else ''])
            break

    if not allowed:
        return jsonify({'ok': False, 'output': 'Command not permitted in restricted admin terminal.'})

    try:
        result = subprocess.run(exec_args, capture_output=True, text=True, timeout=10, shell=False)
        output = (result.stdout or '') + (result.stderr or '')
        return jsonify({'ok': True, 'output': output or 'Command executed successfully.'})
    except Exception as exc:
        return jsonify({'ok': False, 'output': f'Execution failed: {exc}'})


@app.route("/data/<path:filename>")
def serve_data_file(filename):
    """Serve any file from the Data/ directory (songs, images, etc.)"""
    if 'user' not in session:
        abort(401)
    return send_from_directory(str(DATA_DIR), filename)


@app.route("/music/<path:filename>")
def serve_frontend_music(filename):
    """Serve built-in music assets from Frontend/Music."""
    if 'user' not in session:
        abort(401)
    frontend_music = os.path.join(FRONTEND_DIR, "Music")
    return send_from_directory(frontend_music, filename)


@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    """Generate OTP for a registered email/username"""
    data = request.get_json() or {}
    identifier = (data.get('email') or data.get('username') or '').strip().lower()
    if not identifier:
        return jsonify({'success': False, 'message': 'Email or username required'}), 400

    user = get_user_by_email(identifier)
    if not user:
        return jsonify({'success': False, 'message': 'No account found with that email/username'}), 404

    if user.get('username') == 'admin' or user.get('role') == 'admin':
        # Admin can reset password now if their email is correct, but let's allow it securely via OTP
        pass

    otp = str(secrets.randbelow(900000) + 100000)
    
    email_sent = send_email_otp(user.get('email'), otp)
    if not email_sent:
        return jsonify({'success': False, 'message': 'Failed to send OTP email. Please try again.'}), 500

    session['reset_otp'] = otp
    session['reset_user'] = user.get('username')
    session['reset_email'] = user.get('email')
    session['reset_attempts'] = 0
    return jsonify({'success': True, 'message': 'OTP sent to your registered email'})


@app.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    data = request.get_json() or {}
    entered_otp = (data.get('otp') or '').strip()
    new_password = data.get('password', '')
    req_email = (data.get('email') or '').strip().lower()

    if not req_email or not entered_otp or not new_password:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    try:
        from Backend.Database.supabase_client import supabase
        if not supabase:
            raise Exception("Supabase not configured")

        res = supabase.auth.verify_otp({"email": req_email, "token": entered_otp, "type": "recovery"})
        if not getattr(res, 'session', None):
            raise Exception("Invalid OTP")
            
        supabase.auth.set_session(res.session.access_token, res.session.refresh_token)
        supabase.auth.update_user({"password": new_password})
        
        return jsonify({'success': True, 'redirect': '/login'})
    except Exception as e:
        app.logger.error(f"Reset error: {e}")
        return jsonify({'success': False, 'message': 'Invalid OTP or reset failed'}), 401


@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'service': 'shadow-os'})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user' not in session:
        return jsonify({'success': False, 'response': 'Authentication required.', 'error_code': 'unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    message = str(data.get('message') or '').strip()
    if not message:
        return jsonify({'success': False, 'response': 'Message is required.', 'error_code': 'invalid_input'}), 400

    retry_wait = _check_server_cooldown()
    if retry_wait > 0:
        return jsonify({'success': False, 'response': 'Please wait a moment before sending another request.', 'error_code': 'rate_limited'}), 429

    user_id = session.get('user_id')
    task_type = 'general'
    try:
        classifier = FirstLayerDMM(message, user_id=user_id)
        if isinstance(classifier, list) and classifier:
            task_type = str(classifier[0]).strip().lower().replace(' ', '_')
        elif isinstance(classifier, str) and classifier.strip():
            task_type = classifier.strip().lower().replace(' ', '_')
    except Exception as exc:
        app.logger.warning('Chat classifier failed: %s', exc)

    try:
        if task_type in ('realtime', 'google_search', 'youtube_search'):
            response = realtime_search(message, user_id=user_id)
        elif task_type == 'generate_image':
            from Backend.ImageGeneration import generate_images
            generated = generate_images(message)
            response = 'Image generation started.' if generated else 'Image generation failed.'
        else:
            response = ChatBot(message, user_id=user_id, save_history=False)

        if user_id:
            save_chat_message(user_id, 'user', message)
            save_chat_message(user_id, 'assistant', response)

        return jsonify({'success': True, 'response': response, 'task_type': task_type or 'general'})
    except Exception as exc:
        app.logger.exception('Chat route failed for user_id=%s', user_id)
        return jsonify({'success': False, 'response': 'I could not process that request right now. Please try again.', 'error_code': 'chat_error'}), 500


@app.route('/api/network')
def api_network():
    try:
        local_ip = '127.0.0.1'
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                local_ip = sock.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'

        public_ip = 'N/A'
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=3).text.strip() or 'N/A'
        except Exception:
            public_ip = 'N/A'

        wifi = 'N/A'
        if platform.system().lower() == 'windows':
            try:
                netsh = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, timeout=4)
                data = (netsh.stdout or '') + (netsh.stderr or '')
                match = re.search(r'SSID\s*:\s*(.+)', data, re.I)
                if match:
                    wifi = match.group(1).strip()
            except Exception:
                wifi = 'N/A'

        connection = 'Online' if public_ip != 'N/A' or local_ip else 'Offline'
        return jsonify({
            'connection': connection,
            'ip': local_ip,
            'public_ip': public_ip,
            'bandwidth': 'N/A',
            'wifi': wifi,
            'interface': 'Ethernet',
            'status': 'online' if connection == 'Online' else 'offline',
        })
    except Exception as exc:
        app.logger.warning('Network route failed: %s', exc)
        return jsonify({'connection': 'Offline', 'ip': 'N/A', 'public_ip': 'N/A', 'bandwidth': 'N/A', 'wifi': 'N/A', 'interface': 'N/A', 'status': 'offline'})


@app.route('/api/weather')
def api_weather():
    weather_key = get_env('WEATHER_API_KEY')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    city = 'Local Sensor'

    if not weather_key:
        return jsonify({'available': False, 'city': city, 'status': 'Unavailable', 'temperature': '--°C', 'feels_like': 'N/A', 'wind': 'N/A', 'humidity': 'N/A'})

    try:
        if lat and lon:
            geo = {'lat': lat, 'lon': lon}
        else:
            geo_response = requests.get('https://ipinfo.io/json', timeout=3)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            loc = geo_data.get('loc')
            if not loc:
                raise ValueError('Location unavailable')
            lat, lon = loc.split(',')
            geo = {'lat': lat.strip(), 'lon': lon.strip()}
        url = 'https://api.openweathermap.org/data/2.5/weather'
        resp = requests.get(url, params={'lat': geo['lat'], 'lon': geo['lon'], 'appid': weather_key, 'units': 'metric'}, timeout=5)
        resp.raise_for_status()
        payload = resp.json()
        city = payload.get('name') or city
        weather = payload.get('weather', [{}])[0]
        main = payload.get('main', {})
        wind = payload.get('wind', {})
        return jsonify({
            'available': True,
            'city': city,
            'temperature': f"{main.get('temp', '--')}°C",
            'feels_like': f"{main.get('feels_like', 'N/A')}°C",
            'status': weather.get('main') or 'Active',
            'description': weather.get('description') or 'Clear',
            'wind': f"{wind.get('speed', 'N/A')} km/h",
            'humidity': f"{main.get('humidity', 'N/A')}%",
        })
    except Exception as exc:
        app.logger.warning('Weather route failed: %s', exc)
        return jsonify({'available': False, 'city': city, 'status': 'Unavailable', 'temperature': '--°C', 'feels_like': 'N/A', 'wind': 'N/A', 'humidity': 'N/A'})


@app.route('/api/tts', methods=['POST'])
def api_tts():
    data = request.get_json(silent=True) or {}
    text = str(data.get('text') or '').strip()
    if not text:
        return jsonify({'ok': False, 'message': 'Text is required'}), 400

    try:
        from Backend.TextToSpeech import generate_audio_file
        import uuid
        voice = data.get('voice') or get_env('ASSISTANT_VOICE') or None
        language = data.get('language') or get_env('INPUT_LANGUAGE') or 'en'
        gender = data.get('gender') or 'female'
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        generated_path = generate_audio_file(text, voice=voice, language=language, gender=gender, output_name=filename)
        rel_path = Path(generated_path).relative_to(Path(__file__).resolve().parent / 'Data')
        return jsonify({'ok': True, 'audio_url': f'/data/{rel_path.as_posix()}'}), 200
    except Exception as exc:
        app.logger.exception('TTS route failed')
        return jsonify({'ok': False, 'message': 'TTS generation failed'}), 500


@app.route('/api/history')
def api_history():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not found'}), 401

    try:
        from Backend.Database.chat_db import get_chat_history_for_display
        filter_date = request.args.get('date')
        entries = get_chat_history_for_display(user_id, filter_date)
        return jsonify(entries)
    except Exception as exc:
        app.logger.warning('History fetch failed: %s', exc)
        return jsonify([])


@app.route('/api/get-env')
def api_get_env():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    allowed_keys = ['GROQ_API_KEY', 'COHERE_API_KEY', 'HUGGINGFACE_API_KEY', 'WEATHER_API_KEY', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID', 'USERNAME', 'ASSISTANT_NAME', 'INPUT_LANGUAGE', 'ASSISTANT_VOICE']
    payload = {}
    for key in allowed_keys:
        value = get_env(key)
        payload[key] = {'configured': bool(value), 'masked': mask_secret(value) if value else ''}
    return jsonify(payload)


@app.route('/api/update-env', methods=['POST'])
def api_update_env():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    data = request.get_json(silent=True) or {}
    key = str(data.get('key') or '').strip()
    value = str(data.get('value') or '').strip()

    allowed_keys = {'GROQ_API_KEY', 'COHERE_API_KEY', 'HUGGINGFACE_API_KEY', 'WEATHER_API_KEY', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID', 'USERNAME', 'ASSISTANT_NAME', 'INPUT_LANGUAGE', 'ASSISTANT_VOICE'}
    blocked_keys = {'DATABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'SECRET_KEY', 'SMTP_PASSWORD'}

    if key not in allowed_keys or key in blocked_keys:
        return jsonify({'success': False, 'message': 'Key not allowed'}), 400

    if not key:
        return jsonify({'success': False, 'message': 'Missing key'}), 400

    try:
        from dotenv import set_key
        set_key(str(ENV_PATH), key, value)
        os.environ[key] = value
        return jsonify({'success': True, 'message': 'Environment updated successfully'})
    except Exception as exc:
        app.logger.warning('Failed to update env key %s: %s', key, exc)
        return jsonify({'success': False, 'message': 'Could not update environment'}), 500


if __name__ == '__main__':
    _port = int(get_env('PORT', '5000'))
    _host = get_env('HOST', '0.0.0.0')
    _debug = str(os.getenv('FLASK_DEBUG', 'false')).lower() in ('1', 'true', 'yes')
    print("Database: connected" if database_is_available() else "Database: unavailable")
    print(f"Starting Shadow OS on {_host}:{_port} (debug={_debug})")
    app.run(host=_host, port=_port, debug=_debug)



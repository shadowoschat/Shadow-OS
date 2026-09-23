import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from Backend.Database.connection import get_db_cursor
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
load_dotenv(str(BASE_DIR / ".env"))

def migrate_users():
    users_file = DATA_DIR / "users.json"
    if not users_file.exists():
        print("No users.json found.")
        return {}

    with open(users_file, "r") as f:
        users_data = json.load(f)

    # Dictionary mapping username to user_id to resolve links
    user_map = {}

    with get_db_cursor(commit=True) as cursor:
        for u in users_data:
            # Hash password if needed
            pw_hash = u.get("password_hash", "")
            if pw_hash and not (pw_hash.startswith("scrypt:") or pw_hash.startswith("pbkdf2:")):
                # Use a dummy password to replace old legacy ones if salt is involved
                # or just keep it and they can't login. We will generate a random hash just to keep it secure
                pw_hash = generate_password_hash("default_migrate")

            email = u.get("email", "").lower()
            username = u.get("username", "").lower()
            
            try:
                cursor.execute(
                    """
                    INSERT INTO users (first_name, last_name, email, username, password_hash, role, is_verified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (u.get("first", ""), u.get("last", ""), email, username, pw_hash, u.get("role", "user"), u.get("is_verified", True))
                )
                user_id = cursor.fetchone()[0]
                user_map[username] = str(user_id)
                print(f"Migrated user {username}")
            except Exception as e:
                print(f"Skipping user {username}, likely exists: {e}")
                cursor.connection.rollback()
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                row = cursor.fetchone()
                if row:
                    user_map[username] = str(row[0])

    return user_map


def migrate_logins(user_map):
    file = DATA_DIR / "login_history.json"
    if not file.exists():
        return
        
    with open(file, "r") as f:
        data = json.load(f)
        
    with get_db_cursor(commit=True) as cursor:
        for item in data:
            uname = item.get("username", "unknown")
            uid = user_map.get(uname)
            if uid:
                cursor.execute(
                    """
                    INSERT INTO login_history (user_id, success, details, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (uid, item.get("success", False), item.get("details", ""), item.get("ip_address", ""), item.get("user_agent", ""))
                )

def migrate_chats_and_memory(user_map):
    admin_id = user_map.get("admin")
    if not admin_id:
        print("No admin user found to assign legacy data.")
        return
        
    # ChatLog
    chat_file = DATA_DIR / "ChatLog.json"
    if chat_file.exists():
        with open(chat_file, "r") as f:
            data = json.load(f)
        with get_db_cursor(commit=True) as cursor:
            for item in data:
                cursor.execute(
                    "INSERT INTO chat_history (user_id, role, message) VALUES (%s, %s, %s)",
                    (admin_id, item.get("role", "user"), item.get("content", ""))
                )
                
    # Memory
    mem_file = DATA_DIR / "Memory.json"
    if mem_file.exists():
        with open(mem_file, "r") as f:
            data = json.load(f)
        with get_db_cursor(commit=True) as cursor:
            for item in data.get("interactions", []):
                cursor.execute(
                    "INSERT INTO memory (user_id, memory_type, content) VALUES (%s, 'interaction', %s)",
                    (admin_id, json.dumps(item))
                )
            for item in data.get("short_term_memory", []):
                cursor.execute(
                    "INSERT INTO memory (user_id, memory_type, content) VALUES (%s, 'short_term', %s)",
                    (admin_id, json.dumps(item))
                )

if __name__ == "__main__":
    print("Starting migration...")
    user_map = migrate_users()
    migrate_logins(user_map)
    migrate_chats_and_memory(user_map)
    print("Migration complete!")

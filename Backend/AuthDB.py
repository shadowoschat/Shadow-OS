import os
from werkzeug.security import generate_password_hash, check_password_hash
from .Database.connection import get_db_cursor
import psycopg2


def _get_owner_credentials():
    from Backend.config import get_env

    email = get_env("OWNER_EMAIL")
    username = get_env("OWNER_USERNAME")
    password = get_env("OWNER_PASSWORD")
    return email, username, password


def ensure_owner_account(first_name: str = "Admin", last_name: str = "User",
                        email: str = None, username: str = None, password: str = None):
    """Ensure the required owner/admin account exists from environment configuration only."""
    email_value, username_value, password_value = _get_owner_credentials()
    email = (email or email_value or "").strip()
    username = (username or username_value or "").strip()
    password = password or password_value or ""

    if not email or not username or not password:
        return False

    email_norm = email.lower()
    username_norm = username.lower()
    password_hash = generate_password_hash(password)

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM users
                WHERE lower(email) = %s OR lower(username) = %s
                LIMIT 1
                """,
                (email_norm, username_norm)
            )
            row = cursor.fetchone()

            if row:
                cursor.execute(
                    """
                    UPDATE users
                    SET first_name = %s,
                        last_name = %s,
                        email = %s,
                        username = %s,
                        password_hash = %s,
                        role = 'admin',
                        status = 'active',
                        plan = COALESCE(plan, 'pro'),
                        is_verified = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (first_name, last_name, email_norm, username_norm, password_hash, row[0])
                )
                return True

            cursor.execute(
                """
                INSERT INTO users (first_name, last_name, email, username, password_hash, role, status, plan, is_verified)
                VALUES (%s, %s, %s, %s, %s, 'admin', 'active', 'pro', TRUE)
                """,
                (first_name, last_name, email_norm, username_norm, password_hash)
            )
            return True
    except psycopg2.IntegrityError:
        # Another race during creation; then reconcile the existing record.
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET first_name = %s,
                    last_name = %s,
                    email = %s,
                    username = %s,
                    password_hash = %s,
                    role = 'admin',
                    status = 'active',
                    plan = COALESCE(plan, 'pro'),
                    is_verified = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE lower(email) = %s OR lower(username) = %s
                """,
                (first_name, last_name, email_norm, username_norm, password_hash, email_norm, username_norm)
            )
        return True


def list_users():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def create_user(first: str, last: str, email: str, username: str, password: str, role: str = 'user', is_verified: bool = False):
    email_norm = (email or "").strip().lower()
    username_norm = (username or "").strip().lower()

    if not email_norm or not username_norm:
        raise ValueError("Email and username are required")

    pwd_hash = generate_password_hash(password)

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO users (first_name, last_name, email, username, password_hash, role, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (first, last, email_norm, username_norm, pwd_hash, role, is_verified)
            )
        return True
    except psycopg2.IntegrityError as e:
        if "users_email_key" in str(e):
            raise ValueError("Email already exists")
        elif "users_username_key" in str(e):
            raise ValueError("Username already exists")
        else:
            raise ValueError("Database constraint error")

def verify_user(identifier: str, password: str) -> dict | None:
    ident = (identifier or "").strip().lower()
    
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, first_name, last_name, email, username, password_hash, role, is_verified, plan, status 
            FROM users 
            WHERE lower(email) = %s OR lower(username) = %s
            """,
            (ident, ident)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
            
        columns = [desc[0] for desc in cursor.description]
        user = dict(zip(columns, row))
        
        expected_hash = user.get("password_hash", "")
        
        # We assume legacy hashes are handled during the migration script and we only have werkzeug hashes now.
        if expected_hash and check_password_hash(expected_hash, password):
            # Update last_login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))
            
            # id is UUID in db, let's cast to string for session serialization
            user['id'] = str(user['id'])
            
            # Clean up hash before returning
            user.pop('password_hash', None)
            return user
            
    return None

def update_user_password(identifier: str, new_password: str):
    ident = (identifier or "").strip().lower()
    pwd_hash = generate_password_hash(new_password)
    
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE users SET password_hash = %s
            WHERE lower(email) = %s OR lower(username) = %s
            """,
            (pwd_hash, ident, ident)
        )
        return cursor.rowcount > 0

def verify_user_exists(email: str) -> bool:
    email_norm = (email or "").strip().lower()
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM users WHERE lower(email) = %s", (email_norm,))
        return cursor.fetchone() is not None

def get_user_by_email(email: str):
    email_norm = (email or "").strip().lower()
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, first_name, last_name, email, username, role, is_verified, plan, status FROM users WHERE lower(email) = %s", 
            (email_norm,)
        )
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            user = dict(zip(columns, row))
            user['id'] = str(user['id'])
            return user
    return None

def get_user_by_id(user_id: str):
    if not user_id:
        return None
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, first_name, last_name, email, username, role, is_verified, plan, status, created_at, last_login FROM users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            user = dict(zip(columns, row))
            user['id'] = str(user['id'])
            return user
    return None

def mark_user_verified(email: str):
    email_norm = (email or "").strip().lower()
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE users SET is_verified = true WHERE lower(email) = %s", (email_norm,))
        return cursor.rowcount > 0

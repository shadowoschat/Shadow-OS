from .connection import get_db_cursor
from typing import Dict, Any, List, Optional
import datetime
import logging

logger = logging.getLogger(__name__)


def record_login_event(user_id: Optional[str] = None, success: bool = False,
                       details: str = '', ip_address: str = '',
                       user_agent: str = '') -> None:
    """Record a login event. user_id can be None for failed logins where user is unknown."""
    try:
        # If user_id looks like a username/email (not a UUID), set it to None
        if user_id and len(str(user_id)) < 30 and '-' not in str(user_id):
            user_id = None
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO login_history (user_id, success, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, success, details, ip_address or '', user_agent or '')
            )
    except Exception as e:
        logger.error(f"Failed to record login event: {e}")


def record_system_event(admin_user_id: Optional[str] = None, title: str = '',
                        details: str = '', severity: str = 'INFO') -> None:
    """Record an admin/system event. admin_user_id can be None for system-level events."""
    try:
        # If admin_user_id looks like a severity string, treat it as None
        if admin_user_id and len(str(admin_user_id)) < 30 and '-' not in str(admin_user_id):
            admin_user_id = None
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO admin_events (admin_user_id, action, details, status)
                VALUES (%s, %s, %s, %s)
                """,
                (admin_user_id, title, details, severity)
            )
    except Exception as e:
        logger.error(f"Failed to record system event: {e}")


def get_dashboard_stats() -> Dict[str, Any]:
    stats = {
        'total_users': 0,
        'active_users': 0,
        'blocked_users': 0,
        'recent_users': 0
    }
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            stats['active_users'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'blocked'")
            stats['blocked_users'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > CURRENT_DATE - INTERVAL '7 days'")
            stats['recent_users'] = cursor.fetchone()[0] or 0
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
    return stats


def get_all_users() -> List[Dict[str, Any]]:
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, first_name, last_name, email, username, role, plan, status, is_verified, created_at, last_login
                FROM users
                ORDER BY created_at DESC
                """
            )
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            users = []
            for row in rows:
                user_dict = dict(zip(columns, row))
                for k, v in user_dict.items():
                    if isinstance(v, datetime.datetime):
                        user_dict[k] = v.isoformat() + 'Z'
                    elif k == 'id':
                        user_dict[k] = str(v)
                users.append(user_dict)
            return users
    except Exception as e:
        logger.error(f"Failed to get all users: {e}")
        return []


def get_recent_logins(limit: int = 20) -> List[Dict[str, Any]]:
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT l.created_at, u.username, l.success, l.details, l.ip_address, l.user_agent
                FROM login_history l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.created_at DESC LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            entries = []
            for row in rows:
                entries.append({
                    'timestamp': row[0].isoformat() + 'Z' if row[0] else None,
                    'user': row[1] or 'unknown',
                    'username': row[1] or 'unknown',
                    'success': row[2],
                    'details': row[3],
                    'ip_address': row[4],
                    'user_agent': row[5] or 'unknown',
                })
            return entries
    except Exception as e:
        logger.error(f"Failed to get recent logins: {e}")
        return []


def get_recent_admin_events(limit: int = 20) -> List[Dict[str, Any]]:
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT e.created_at, u.username, e.action, e.status, e.details
                FROM admin_events e
                LEFT JOIN users u ON e.admin_user_id = u.id
                ORDER BY e.created_at DESC LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            entries = []
            for row in rows:
                entries.append({
                    'timestamp': row[0].isoformat() + 'Z' if row[0] else None,
                    'user': row[1] or 'system',
                    'action': row[2],
                    'status': row[3],
                    'details': row[4]
                })
            return entries
    except Exception as e:
        logger.error(f"Failed to get recent admin events: {e}")
        return []


# ---- Device management via PostgreSQL ----

def load_devices_db(user_id: Optional[str] = None) -> List[str]:
    """Load authorized device names. If user_id is provided, load for that user only."""
    try:
        with get_db_cursor() as cursor:
            if user_id:
                cursor.execute("SELECT device_name FROM devices WHERE user_id = %s", (user_id,))
            else:
                cursor.execute("SELECT device_name FROM devices")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to load devices: {e}")
        return []


def save_device_db(user_id: str, device_name: str) -> None:
    """Save a new authorized device for the user (skip if already exists)."""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "SELECT 1 FROM devices WHERE user_id = %s AND device_name = %s",
                (user_id, device_name)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO devices (user_id, device_name) VALUES (%s, %s)",
                    (user_id, device_name)
                )
    except Exception as e:
        logger.error(f"Failed to save device: {e}")


def is_device_authorized_db(device_name: str) -> bool:
    """Check if a device name is authorized for any user."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1 FROM devices WHERE device_name = %s LIMIT 1", (device_name,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Failed to check device: {e}")
        return False


def update_user_by_admin(user_id: str, updates: Dict[str, Any]) -> bool:
    """Admin updates a user's fields."""
    try:
        set_parts = []
        values = []
        allowed = ['username', 'email', 'role', 'plan', 'status', 'is_verified']
        for key in allowed:
            if key in updates:
                set_parts.append(f"{key} = %s")
                values.append(updates[key])
        if not set_parts:
            return False
        values.append(user_id)
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                f"UPDATE users SET {', '.join(set_parts)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                values
            )
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        return False


def delete_user_by_admin(user_id: str) -> bool:
    """Admin deletes a user."""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        return False

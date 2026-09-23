from .connection import get_db_cursor
from typing import List, Dict, Any, Optional
import datetime
import logging

logger = logging.getLogger(__name__)


def get_chat_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get the recent chat history for a specific user (for LLM context)."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT role, message as content
                FROM chat_history
                WHERE user_id = %s
                ORDER BY created_at ASC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
            return [{"role": row[0], "content": row[1]} for row in rows[-limit:]]
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        return []


def save_chat_message(user_id: str, role: str, message: str) -> None:
    """Save a single chat message."""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO chat_history (user_id, role, message)
                VALUES (%s, %s, %s)
                """,
                (user_id, role, message)
            )
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}")


def get_chat_history_for_display(user_id: str, filter_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get full chat history for the history panel.
    Returns paired user+assistant messages with timestamps.
    filter_date: optional YYYY-MM-DD string to filter by date.
    """
    try:
        with get_db_cursor() as cursor:
            if filter_date:
                cursor.execute(
                    """
                    SELECT role, message, created_at
                    FROM chat_history
                    WHERE user_id = %s AND DATE(created_at) = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id, filter_date)
                )
            else:
                cursor.execute(
                    """
                    SELECT role, message, created_at
                    FROM chat_history
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id,)
                )
            rows = cursor.fetchall()

            # Build paired entries: group consecutive user+assistant pairs
            results = []
            i = 0
            # rows are in DESC order, so newest first
            # We need to pair them: each assistant response with the preceding user message
            # Reverse to process chronologically, then re-reverse
            rows_asc = list(reversed(rows))
            while i < len(rows_asc):
                row = rows_asc[i]
                if row[0] == 'user' and i + 1 < len(rows_asc) and rows_asc[i + 1][0] == 'assistant':
                    ts = row[2]
                    readable_date = ts.strftime('%Y-%m-%d') if isinstance(ts, datetime.datetime) else str(ts)[:10]
                    results.append({
                        'user_msg': row[1],
                        'response': rows_asc[i + 1][1],
                        'timestamp': ts.timestamp() if isinstance(ts, datetime.datetime) else 0,
                        'date': readable_date,
                    })
                    i += 2
                else:
                    i += 1

            # Return newest-first
            results.reverse()
            return results
    except Exception as e:
        logger.error(f"Failed to get chat history for display: {e}")
        return []

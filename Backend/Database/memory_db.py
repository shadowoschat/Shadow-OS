import json
from .connection import get_db_cursor
from typing import Dict, Any, List

def get_user_memory(user_id: str) -> Dict[str, Any]:
    """Fetch all memory components for a user and format them like the old JSON structure."""
    memory_dict = {
        "user_name": "User", # Will be overridden if we join with users table
        "short_term_memory": [],
        "interactions": []
    }
    
    with get_db_cursor() as cursor:
        # Get username
        cursor.execute("SELECT first_name FROM users WHERE id = %s", (user_id,))
        user_row = cursor.fetchone()
        if user_row and user_row[0]:
            memory_dict["user_name"] = user_row[0]
            
        # Get memories
        cursor.execute(
            """
            SELECT memory_type, content 
            FROM memory 
            WHERE user_id = %s
            ORDER BY created_at ASC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        for m_type, content in rows:
            if m_type == 'short_term':
                memory_dict["short_term_memory"].append(content)
            elif m_type == 'interaction':
                memory_dict["interactions"].append(content)
                
    return memory_dict

def save_interaction(user_id: str, content: Dict[str, Any]) -> None:
    """Save an interaction memory."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO memory (user_id, memory_type, content)
            VALUES (%s, %s, %s)
            """,
            (user_id, 'interaction', json.dumps(content))
        )
        
        # Keep only last 100 interactions
        cursor.execute(
            """
            DELETE FROM memory 
            WHERE id IN (
                SELECT id FROM memory 
                WHERE user_id = %s AND memory_type = 'interaction'
                ORDER BY created_at DESC 
                OFFSET 100
            )
            """,
            (user_id,)
        )

def save_short_term_memory(user_id: str, content: Dict[str, Any]) -> None:
    """Save short term memory."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO memory (user_id, memory_type, content)
            VALUES (%s, %s, %s)
            """,
            (user_id, 'short_term', json.dumps(content))
        )

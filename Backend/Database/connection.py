import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Robust .env loading: prefer project root .env so DB modules work even when
# imported before the main app has a chance to call load_dotenv(). This avoids
# timing/order issues when `Backend` modules are imported at module import time.
try:
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(str(env_path), override=False)
        logger.debug("Loaded .env from project root: %s", str(env_path))
    else:
        load_dotenv(override=False)
except Exception as ex:
    logger.debug("Failed to load .env automatically: %s", ex)

_pool = None


def get_database_url():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not configured. Ensure a .env with DATABASE_URL exists at the project root.")

    parsed = urlparse(db_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must use a PostgreSQL scheme.")
    if not parsed.hostname or not parsed.path or parsed.path == "/":
        raise ValueError("DATABASE_URL is missing host or database name.")
    return db_url


def database_is_available():
    try:
        db_url = get_database_url()
        with psycopg2.connect(db_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def get_connection_pool():
    global _pool
    if _pool is None:
        db_url = get_database_url()
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(1, 10, db_url)
        except Exception as e:
            msg = (
                "Postgres connection failed. Check DATABASE_URL in your .env "
                "(user, password, host, port, dbname). Original error: {}".format(e)
            )
            raise RuntimeError(msg) from e
    return _pool

def get_db_connection():
    """Get a connection from the pool."""
    pool = get_connection_pool()
    return pool.getconn()

def release_db_connection(conn):
    """Return a connection to the pool."""
    if _pool and conn:
        _pool.putconn(conn)

class get_db_cursor:
    """Context manager for easily getting a cursor and committing/rolling back."""
    def __init__(self, commit=False):
        self.commit = commit
        self.conn = None
        self.cursor = None
        
    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self.cursor
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
        elif self.commit:
            self.conn.commit()
            
        if self.cursor:
            self.cursor.close()
        release_db_connection(self.conn)

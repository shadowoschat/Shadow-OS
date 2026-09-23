"""
Apply `database/schema.sql` to the database referenced by DATABASE_URL.
Run: python scripts/apply_schema.py
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import psycopg2
except Exception:
    print("psycopg2 is required. Install with: pip install psycopg2-binary")
    raise

from dotenv import load_dotenv


def mask_database_url(value: str) -> str:
    if not value:
        return "<unset>"
    parsed = urlparse(value)
    host = parsed.hostname or "<host>"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or "/<database>"
    if parsed.username:
        user = parsed.username[:2] + "***" if len(parsed.username) > 2 else "***"
        return f"{parsed.scheme}://{user}@{host}{port}{path}"
    return f"{parsed.scheme}://{host}{port}{path}"


base = Path(__file__).resolve().parents[1]
schema_file = base / "database" / "schema.sql"
if not schema_file.exists():
    print("schema.sql not found at", str(schema_file))
    sys.exit(1)

# Load .env from project root if present so DATABASE_URL is available
env_path = base / ".env"
if env_path.exists():
    load_dotenv(str(env_path), override=False)

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL is not set. Set it in environment or in .env and reload.")
    sys.exit(1)

print("Applying schema from:", schema_file)
print("Using configured DATABASE_URL from environment.")
print(f"Database URL fingerprint: {mask_database_url(db_url)}")

sql = schema_file.read_text()

conn = None
try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    print("Schema applied successfully.")
except Exception as e:
    print("Failed to apply schema:", e)
    raise
finally:
    if conn:
        conn.close()

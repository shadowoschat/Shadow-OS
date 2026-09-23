import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT id, first_name, last_name, email, username, role, status, plan, is_verified FROM users ORDER BY created_at')
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()

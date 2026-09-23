import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL is not set')

pwd_hash = generate_password_hash('379037@')

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id FROM users
        WHERE lower(email) = lower(%s)
           OR lower(username) = lower(%s)
        ORDER BY created_at ASC
        LIMIT 1
        """,
        ('shadowai3846@gmail.com', 'Shadow@123'),
    )
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE users
            SET first_name = %s,
                last_name = %s,
                email = %s,
                username = %s,
                password_hash = %s,
                role = 'admin',
                status = 'active',
                plan = 'pro',
                is_verified = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            ('suraj', 'pawar', 'shadowai3846@gmail.com', 'shadow@123', pwd_hash, row[0]),
        )
        print('updated owner account')
    else:
        cur.execute(
            """
            INSERT INTO users (first_name, last_name, email, username, password_hash, role, status, plan, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            ('suraj', 'pawar', 'shadowai3846@gmail.com', 'shadow@123', pwd_hash, 'admin', 'active', 'pro'),
        )
        print('created owner account')

    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()

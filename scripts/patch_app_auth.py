import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# I will replace from @app.route("/api/login") down to the end of clear_otp()
auth_block = """
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
        session['role'] = role
        session['access_token'] = auth_res.session.access_token
        
        record_login_event(user_id, success=True, details='User login via Supabase', ip_address=request.remote_addr)
        return jsonify({'success': True, 'redirect': '/admin' if role == 'admin' else '/dashboard'})
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
    return session.get('role') == 'admin'


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
                \"\"\"
                INSERT INTO users (id, first_name, last_name, email, username, role, is_verified, status)
                VALUES (%s, %s, %s, %s, %s, 'user', FALSE, 'active')
                ON CONFLICT (id) DO NOTHING
                \"\"\",
                (str(user.id), first, last, email, username)
            )

        # Instead of our custom OTP, rely on Supabase's email confirmation.
        return jsonify({'success': True, 'redirect': '/login', 'message': 'Registration successful! Please check your email to verify your account.'})
    except Exception as e:
        app.logger.error(f"Signup error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
        
    try:
        if supabase:
            supabase.auth.reset_password_email(email)
        return jsonify({'success': True, 'message': 'If this email is registered, a password reset link has been sent.'})
    except Exception as e:
        app.logger.error(f"Reset password error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500


# Removing old verify and clear_otp routes since Supabase handles email verification
@app.route("/api/verify", methods=["POST"])
def api_verify():
    return jsonify({'success': False, 'message': 'Use email link to verify.'}), 400

@app.route("/api/clear-otp", methods=["POST"])
def clear_otp():
    return jsonify({'success': True})
"""

# Regex substitution
pattern = re.compile(r'@app\.route\("/api/login", methods=\["POST"\]\).*?def clear_otp\(\):.*?return jsonify\(\{.*?\}\)', re.DOTALL)
new_content = pattern.sub(auth_block, content)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Auth routes patched.")

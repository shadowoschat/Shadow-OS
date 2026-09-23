import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

reset_block = """
@app.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    data = request.get_json() or {}
    entered_otp = (data.get('otp') or '').strip()
    new_password = data.get('password', '')
    req_email = (data.get('email') or '').strip().lower()

    if not req_email or not entered_otp or not new_password:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    try:
        from Backend.Database.supabase_client import supabase
        if not supabase:
            raise Exception("Supabase not configured")

        # 1. Verify OTP to get session
        res = supabase.auth.verify_otp({"email": req_email, "token": entered_otp, "type": "recovery"})
        if not getattr(res, 'session', None):
            raise Exception("Invalid OTP")
            
        # 2. Update password
        supabase.auth.set_session(res.session.access_token, res.session.refresh_token)
        update_res = supabase.auth.update_user({"password": new_password})
        
        return jsonify({'success': True, 'redirect': '/login'})
    except Exception as e:
        app.logger.error(f"Reset error: {e}")
        return jsonify({'success': False, 'message': 'Invalid OTP or reset failed'}), 401
"""

pattern = re.compile(r'@app\.route\("/api/reset-password", methods=\["POST"\]\).*?def api_reset_password\(\):.*?return jsonify\(\{\'success\': True, \'redirect\': \'/login\'\}\)', re.DOTALL)
new_content = pattern.sub(reset_block, content)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Reset password route patched.")

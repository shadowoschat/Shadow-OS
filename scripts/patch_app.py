import re
from pathlib import Path

def patch_app_py():
    path = Path('app.py')
    content = path.read_text(encoding='utf-8')
    
    # 1. Imports
    imports_to_add = """
from Backend.Database.chat_db import get_chat_history, save_chat_message
from Backend.Database.memory_db import get_user_memory, save_interaction, save_short_term_memory
from Backend.Database.admin_db import get_dashboard_stats, get_all_users, get_recent_logins, get_recent_admin_events, record_login_event, record_system_event
"""
    # Just insert it before `# -----------------------------` of ENV & PATH SETUP
    content = content.replace("# -----------------------------\n# ENV & PATH SETUP", imports_to_add + "\n# -----------------------------\n# ENV & PATH SETUP")
    
    # 2. Fix the login route to set user_id
    content = content.replace("session['user'] = user.get('username')", "session['user'] = user.get('username')\n        session['user_id'] = user.get('id')")
    content = content.replace("session['pending_user'] = user.get('username')", "session['pending_user'] = user.get('username')\n    session['pending_user_id'] = user.get('id')")
    content = content.replace("session['user'] = session['pending_user']", "session['user'] = session['pending_user']\n        session['user_id'] = session.get('pending_user_id')")
    
    # 3. record_login_event and record_system_event
    # We already have new ones in admin_db, so we'll replace the calls.
    content = content.replace("record_login_event(session['user'], success=True,", "record_login_event(session.get('user_id'), success=True,")
    content = content.replace("record_login_event(session.get('pending_user', 'unknown'), success=False,", "record_login_event(session.get('pending_user_id'), success=False,")
    content = content.replace("record_system_event('INFO', 'Logout', f\"{session.get('user')} logged out\", 'INFO')", "record_system_event(session.get('user_id'), 'Logout', f\"{session.get('user')} logged out\", 'INFO')")
    content = content.replace("record_system_event('WARNING', 'Login Failed', f\"Failed login for {username}\", 'WARNING')", "record_system_event(None, 'Login Failed', f\"Failed login for {username}\", 'WARNING')")
    
    # 4. Remove old json append list and event recorders
    old_funcs = re.search(r"def _append_json_list\(.*?def record_system_event.*?_append_json_list\(ADMIN_EVENTS_FILE, entry\)", content, re.DOTALL)
    if old_funcs:
        content = content.replace(old_funcs.group(0), "")
        
    # 5. Remove file exist checks
    old_files = re.search(r"MEMORY_FILE = DATA_DIR / \"Memory.json\".*?if not ADMIN_EVENTS_FILE.exists\(\):\s*ADMIN_EVENTS_FILE.write_text\('\[\]', encoding='utf-8'\)", content, re.DOTALL)
    if old_files:
        content = content.replace(old_files.group(0), "TTS_AUDIO_FILE = DATA_DIR / \"TTS\" / \"voice.mp3\"")
        
    # 6. Update save_interaction
    old_save_int = re.search(r"def save_interaction\(user_msg, task_type, response\):.*?app\.logger\.error\(f\"Error saving interaction: \{e\}\"\)", content, re.DOTALL)
    if old_save_int:
        new_save_int = """def save_interaction_wrapper(user_id, user_msg, task_type, response):
    try:
        if user_id:
            save_interaction(user_id, {
                "timestamp": time.time(),
                "user_msg": user_msg,
                "task_type": task_type,
                "response": response
            })
    except Exception as e:
        app.logger.error(f"Error saving interaction: {e}")"""
        content = content.replace(old_save_int.group(0), new_save_int)
        
    # 7. Update append_to_backup
    old_backup = re.search(r"def append_to_backup\(user_msg, final_response\):.*?app\.logger\.error\(f\"Backup error: \{e\}\"\)", content, re.DOTALL)
    if old_backup:
        new_backup = """def append_to_backup_wrapper(user_id, user_msg, final_response):
    pass # we handle this inside chatbot now"""
        content = content.replace(old_backup.group(0), new_backup)
        
    # 8. Update save_chat
    old_chat = re.search(r"def save_chat\(user_msg, final_response\):.*?app\.logger\.error\(f\"ChatLog error: \{e\}\"\)", content, re.DOTALL)
    if old_chat:
        new_chat = """def save_chat(user_msg, final_response):
    pass # handled inside chatbot now"""
        content = content.replace(old_chat.group(0), new_chat)
        
    # 9. Update admin panel dashboard route
    old_dashboard = re.search(r"def admin_dashboard\(\):.*?return render_template\('admin_dashboard\.html', \*\*context\)", content, re.DOTALL)
    if old_dashboard:
        new_dashboard = """def admin_dashboard():
    if not is_admin_session():
        abort(403)
    stats = get_dashboard_stats()
    context = {
        'total_users': stats.get('total_users', 0),
        'active_users': stats.get('active_users', 0),
        'blocked_users': stats.get('blocked_users', 0),
        'verified_users': stats.get('active_users', 0), # approx
        'recent_users': stats.get('recent_users', 0),
    }
    return render_template('admin_dashboard.html', **context)"""
        content = content.replace(old_dashboard.group(0), new_dashboard)
        
    # 10. Admin API routes: /api/admin/events, /api/admin/users
    # Replace api_admin_events
    old_events = re.search(r"@app\.route\(\"/api/admin/events\"\).*?return jsonify\(.*?\}\)", content, re.DOTALL)
    if old_events:
        new_events = """@app.route("/api/admin/events")
def api_admin_events():
    if 'user' not in session or not is_admin_session():
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify({
        'devices': [],
        'users': [],
        'logins': get_recent_logins(),
        'system': get_recent_admin_events()
    })"""
        content = content.replace(old_events.group(0), new_events)
        
    # Replace get_users_list
    old_users = re.search(r"@app\.route\(\"/api/admin/users\"\).*?return jsonify\(\{'users': users\}\)", content, re.DOTALL)
    if old_users:
        new_users = """@app.route("/api/admin/users")
def get_users_list():
    if 'user' not in session or not is_admin_session():
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify({'users': get_all_users()})"""
        content = content.replace(old_users.group(0), new_users)
        
    # 11. chat route update
    content = content.replace("response = ChatBot(clean_msg)", "response = ChatBot(clean_msg, user_id=session.get('user_id'))")
    content = content.replace("save_interaction(clean_msg, \"ChatBot\", response)", "save_interaction_wrapper(session.get('user_id'), clean_msg, \"ChatBot\", response)")
    content = content.replace("append_to_backup(clean_msg, response)", "append_to_backup_wrapper(session.get('user_id'), clean_msg, response)")
    
    # Update FirstLayerDMM call
    content = content.replace("tasks = FirstLayerDMM(clean_msg)", "tasks = FirstLayerDMM(clean_msg, user_id=session.get('user_id'))")
    
    # 12. get_memory route
    old_get_mem = re.search(r"def get_memory\(\):.*?except:.*?return jsonify\(\{\"interactions\": \[\]\}\)", content, re.DOTALL)
    if old_get_mem:
        new_get_mem = """def get_memory():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = session.get('user_id')
    return jsonify(get_user_memory(user_id))"""
        content = content.replace(old_get_mem.group(0), new_get_mem)
        
    path.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    patch_app_py()

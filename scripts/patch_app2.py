import re
from pathlib import Path

def patch_app_py2():
    path = Path('app.py')
    content = path.read_text(encoding='utf-8')
    
    # 1. Update /api/admin/overview
    old_overview = re.search(r"@app\.route\(\"/api/admin/overview\"\).*?return jsonify\(\{.*?\}\)", content, re.DOTALL)
    if old_overview:
        new_overview = """@app.route("/api/admin/overview")
def api_admin_overview():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if not is_admin_session():
        return jsonify({'error': 'Forbidden'}), 403

    users = get_all_users()
    for u in users:
        u['name'] = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or 'Unknown'
        u['password_status'] = 'Configured'
        u['login_count'] = 0
        u['created_date'] = u.get('created_at', 'N/A')
        u['current_session'] = 'N/A'

    logins = get_recent_logins(40)
    for l in logins:
        l['login_time'] = l.get('timestamp')
        l['logout_time'] = ''
        l['session_status'] = 'SUCCESS' if l.get('success') else 'FAILED'
        l['result'] = 'SUCCESS' if l.get('success') else 'FAILED'
        l['ip'] = l.get('ip_address')
        l['device'] = l.get('user_agent', 'unknown')[:60]

    events = get_recent_admin_events(30)
    warnings = []
    for e in events:
        warnings.append({
            'timestamp': e.get('timestamp'),
            'severity': e.get('status', 'INFO'),
            'title': e.get('action'),
            'message': e.get('details')
        })

    connections = []
    info = {
        'os': platform.system(),
        'python_version': platform.python_version(),
        'flask_status': 'Running',
        'cpu': f"{platform.processor() or 'Unknown'}",
        'server_status': 'Online',
        'current_user': session.get('user', 'admin'),
        'process_status': 'Nominal',
    }

    return jsonify({
        'users': users,
        'login_history': logins,
        'problems': warnings,
        'ports': connections,
        'system': info,
    })"""
        content = content.replace(old_overview.group(0), new_overview)

    # 2. Update /api/admin/users
    old_admin_users = re.search(r"@app\.route\(\"/api/admin/users\", methods=\[\"GET\", \"POST\", \"PUT\", \"DELETE\"\]\).*?except Exception as e:\s*return jsonify\(\{'success': False, 'message': str\(e\)\}\), 500", content, re.DOTALL)
    if old_admin_users:
        new_admin_users = """@app.route("/api/admin/users", methods=["GET"])
def api_admin_users():
    if not is_admin_session():
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify({'users': get_all_users()})"""
        content = content.replace(old_admin_users.group(0), new_admin_users)

    path.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    patch_app_py2()

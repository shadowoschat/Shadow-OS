import re

with open('Frontend/Templates/dashboard.html', 'r', encoding='utf-8') as f:
    dashboard = f.read()

with open('Frontend/Templates/admin.html', 'r', encoding='utf-8') as f:
    admin = f.read()

# Extract top-navbar from dashboard
top_navbar_match = re.search(r'<header class="top-navbar" id="topNavbar">.*?</header>', dashboard, re.DOTALL)
top_navbar = top_navbar_match.group(0)

# Build the admin sidebar based on the dashboard structure
admin_sidebar = """
    <aside class="sidebar" id="mainSidebar">
      <!-- Clean Top Controls Bar -->
      <div class="sidebar-top-strip">
        <span class="sidebar-title-label">ADMIN CONTROL</span>
        <button class="mobile-sidebar-close" id="mobileSidebarClose" aria-label="Close Sidebar">✕</button>
        <button class="sidebar-toggle-btn" id="sidebarToggleBtn" aria-label="Toggle Sidebar" title="Collapse / Expand Sidebar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
      </div>

      <!-- Navigation Menu -->
      <nav class="sidebar-nav">
        <a href="#" class="nav-item active" data-section="dashboard" data-tooltip="Dashboard">
          <div class="nav-icon"><span style="font-size:1.2rem">⬚</span></div>
          <span class="nav-label">Dashboard</span>
        </a>
        <a href="#" class="nav-item" data-section="users" data-tooltip="Users">
          <div class="nav-icon"><span style="font-size:1.2rem">👤</span></div>
          <span class="nav-label">Users</span>
        </a>
        <a href="#" class="nav-item" data-section="keys" data-tooltip="API Keys">
          <div class="nav-icon"><span style="font-size:1.2rem">🔑</span></div>
          <span class="nav-label">API Keys</span>
        </a>
        <a href="#" class="nav-item" data-section="terminal" data-tooltip="Terminal">
          <div class="nav-icon"><span style="font-size:1.2rem">▶_</span></div>
          <span class="nav-label">Terminal</span>
        </a>
        <a href="#" class="nav-item" data-section="inbox" data-tooltip="Inbox">
          <div class="nav-icon"><span style="font-size:1.2rem">✉</span></div>
          <span class="nav-label">Inbox</span>
        </a>
        <a href="#" class="nav-item" data-section="theme" data-tooltip="Theme">
          <div class="nav-icon"><span style="font-size:1.2rem">◐</span></div>
          <span class="nav-label">Theme</span>
        </a>
        <a href="#" class="nav-item" data-section="sql" data-tooltip="SQL / Database">
          <div class="nav-icon"><span style="font-size:1.2rem">☡</span></div>
          <span class="nav-label">SQL / Database</span>
        </a>
        <a href="#" class="nav-item" data-section="logs" data-tooltip="Data / Logs">
          <div class="nav-icon"><span style="font-size:1.2rem">≡</span></div>
          <span class="nav-label">Data / Logs</span>
        </a>

        <!-- SYSTEM Divider -->
        <div class="nav-section-title">SYSTEM</div>
        <a href="/dashboard" class="nav-item" data-tooltip="User Dashboard">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
          </div>
          <span class="nav-label">User Dashboard</span>
        </a>
      </nav>

      <!-- Sidebar Bottom: Real Logged-in Operator Profile Card (NO LOGOUT BUTTON) -->
      <div class="sidebar-footer">
        <a href="/profile" class="operator-profile-card" title="View Account Profile">
          <div class="operator-avatar">
            <img src="{{ url_for('static', filename='image/robot.svg') }}" alt="Operator Avatar" />
            <span class="operator-online-dot"></span>
          </div>
          <div class="operator-info">
            <span class="operator-name" id="operatorName">Operator</span>
            <span class="operator-email" id="operatorEmail">operator@shadow.os</span>
            <span class="operator-status-badge">
              <span style="width: 5px; height: 5px; border-radius: 50%; background: var(--green);"></span>
              <span id="operatorRole">ADMIN</span>
            </span>
          </div>
        </a>
      </div>
    </aside>
"""

# Extract the content-wrap from admin.html
content_wrap_match = re.search(r'<div class="content-wrap">.*?(?=</main>)', admin, re.DOTALL)
if not content_wrap_match:
    print("Could not find content-wrap in admin.html")
    exit(1)
content_wrap = content_wrap_match.group(0)

# Read the top-header from dashboard
top_header_match = re.search(r'<header class="top-header">.*?</header>', dashboard, re.DOTALL)
top_header = top_header_match.group(0)
# Change the breadcrumb in top-header
top_header = top_header.replace('<span class="current">Dashboard</span>', '<span class="current" id="breadcrumb-section">Admin Dashboard</span>')

new_body_content = f"""
  <div class="mobile-sidebar-backdrop" id="mobileBackdrop"></div>

{top_navbar}

  <div class="app-layout">
{admin_sidebar}

    <div class="main-wrapper">
{top_header}

      <main class="page-container">
{content_wrap}
      </main>
    </div>
  </div>

  <!-- ============ TOAST ============ -->
  <div id="toast" class="toast"></div>

  <!-- ============ MODAL ============ -->
  <div id="modal-backdrop" class="modal-backdrop">
    <div class="modal" id="modal-content"></div>
  </div>

  <script src="{{{{ url_for('static', filename='Js/sidebar.js') }}}}"></script>
  <script src="{{{{ url_for('static', filename='Js/admin.js') }}}}"></script>
"""

# Replace body content
admin_new = re.sub(r'<body>.*?</body>', f'<body>\n{new_body_content}\n</body>', admin, flags=re.DOTALL)

with open('Frontend/Templates/admin.html', 'w', encoding='utf-8') as f:
    f.write(admin_new)

print("admin.html updated successfully!")

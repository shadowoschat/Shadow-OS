/* ============================================
   SHADOW OS — ADMIN PANEL JAVASCRIPT
   Vanilla JS — no frameworks
   ============================================ */

(function () {
  'use strict';

  /* ============ CONFIG ============ */
  var SECTIONS = [
    { key: 'dashboard', label: 'Dashboard', icon: '⬚' },
    { key: 'users', label: 'Users', icon: '👤' },
    { key: 'keys', label: 'API Keys', icon: '🔑' },
    { key: 'terminal', label: 'Terminal', icon: '▶_' },
    { key: 'inbox', label: 'Inbox', icon: '✉' },
    { key: 'theme', label: 'Theme', icon: '◐' },
    { key: 'sql', label: 'SQL / Database', icon: '☡' },
    { key: 'logs', label: 'Data / Logs', icon: '≡' }
  ];

  var THEMES = [
    { key: 'blue', label: 'Shadow Default', desc: 'Blue' },
    { key: 'red', label: 'Cyber / Hacking', desc: 'Dark Red' },
    { key: 'green', label: 'Hacker Green', desc: 'Green' },
    { key: 'purple', label: 'Violet Signal', desc: 'Purple' },
    { key: 'orange', label: 'Solar Flare', desc: 'Orange' },
    { key: 'cyan', label: 'Neon Cyan', desc: 'Cyan' },
    { key: 'pink', label: 'Signal Pink', desc: 'Pink' },
    { key: 'midnight', label: 'Midnight Black', desc: 'Black' },
    { key: 'ice', label: 'Ice / Light', desc: 'Light' },
    { key: 'custom', label: 'Custom', desc: 'Personalized' }
  ];

  var MODEL_OPTIONS = {
    OpenAI: ['GPT-4o', 'GPT-4o mini', 'o3-mini'],
    Gemini: ['Gemini 1.5 Flash', 'Gemini 1.5 Pro', 'Gemini 2.0 Flash'],
    Groq: ['Llama 3.1 70B', 'Mixtral 8x7B', 'Llama 3.1 8B'],
    Cohere: ['Command R+', 'Command R', 'Embed v3'],
    ElevenLabs: ['TTS Multilingual v2', 'Eleven Turbo v2.5', 'Voice Design'],
    DeepSeek: ['DeepSeek R1', 'DeepSeek V3', 'DeepSeek Coder']
  };

  var ROLES = [
    { role: 'Owner', detail: 'Full system access', tone: 'pink' },
    { role: 'Admin', detail: 'Full admin panel access', tone: 'blue' },
    { role: 'Sub Admin', detail: 'Limited admin permissions', tone: 'cyan' },
    { role: 'User', detail: 'Standard user access', tone: 'green' },
    { role: 'Guest', detail: 'Limited access', tone: 'orange' }
  ];

  var INBOX_TABS = ['All', 'User Messages', 'Support', 'Notifications', 'System'];
  var LOG_TABS = ['Chat Logs', 'Command Logs', 'Login History', 'Device History', 'API Logs', 'User Activity', 'Admin Activity', 'System Logs', 'Error Logs'];

  var SYSTEM_SERVICES = ['Main Server', 'Database', 'AI Models', 'Storage', 'API Services', 'Network'];

  /* ============ STATE ============ */
  var activeSection = 'dashboard';
  var activeLogTab = LOG_TABS[0];
  var activeInboxTab = 'All';
  var toastTimer = null;

  /* ============ DOM SHORTCUTS ============ */
  function $(id) { return document.getElementById(id); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  /* ============ INIT ============ */
  function init() {
    buildDashboard();
    buildProviderSelect();
    buildThemeGrid();
    buildInboxTabs();
    buildLogTabs();
    buildRoles();
    buildQuickActions();
    bindNavigation();
    bindSidebar();
    bindTerminal();
    bindModal();
    bindSearch();
    restoreTheme();
    // Fetch live admin overview data from backend
    fetchAdminOverview();
  }

  async function fetchAdminOverview() {
    try {
      const res = await fetch('/api/admin/overview');
      if (!res.ok) return;
      const data = await res.json().catch(() => ({}));

      // Update KPI cards
      const users = data.users || [];
      const kpiGrid = $('kpi-grid');
      if (kpiGrid) {
        kpiGrid.innerHTML = '<div class="kpi-card green"><div class="kpi-icon">👤</div><span>Total Users</span><strong>' + (users.length) + '</strong><small>Connected accounts</small><span class="kpi-arrow">↗</span></div>' +
          '<div class="kpi-card"><div class="kpi-icon">⏱</div><span>Active Users</span><strong>' + (users.filter(u=>u.status==='active').length) + '</strong><small>Active status</small><span class="kpi-arrow">↗</span></div>' +
          '<div class="kpi-card cyan"><div class="kpi-icon">✉</div><span>Recent Logins</span><strong>' + ((data.login_history||[]).length) + '</strong><small>Latest events</small><span class="kpi-arrow">↗</span></div>' +
          '<div class="kpi-card orange"><div class="kpi-icon">⚡</div><span>API Requests</span><strong>' + ((data.system && data.system.api_requests) || 0) + '</strong><small>Usage</small><span class="kpi-arrow">↗</span></div>';
      }

      // Populate users table
      const tbody = $('users-tbody');
      if (tbody) {
        if (users.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">👤</div><strong>No users connected</strong><span>User records will appear here when your identity source is connected.</span></div></td></tr>';
        } else {
          tbody.innerHTML = users.map(u => {
            return '<tr>' +
              '<td>' + (u.id || '') + '</td>' +
              '<td>' + (u.username || '') + '</td>' +
              '<td>' + (u.email || '') + '</td>' +
              '<td>' + (u.role || '') + '</td>' +
              '<td>' + (u.status || '') + '</td>' +
              '<td>' + (u.last_login || 'N/A') + '</td>' +
              '<td><button class="icon-button" onclick="showToast(\'Not implemented\')">⋯</button></td>' +
              '</tr>';
          }).join('');
        }
        const count = $('users-count'); if (count) count.textContent = users.length + ' users';
      }
    } catch (err) {
      console.warn('admin overview fetch failed', err);
    }
  }

  /* ============ NAVIGATION — only one section visible ============ */
  function bindNavigation() {
    $$('.nav-item').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var section = btn.getAttribute('data-section');
        switchSection(section);
      });
    });
  }

  function switchSection(section) {
    activeSection = section;

    // hide all sections
    $$('.content-section').forEach(function (s) { s.classList.remove('active'); });

    // show only the target
    var target = $('section-' + section);
    if (target) target.classList.add('active');

    // update nav active states
    $$('.nav-item').forEach(function (btn) {
      btn.classList.toggle('active', btn.getAttribute('data-section') === section);
    });

    // update breadcrumb
    var crumb = $('breadcrumb-section');
    if (crumb) {
      var match = SECTIONS.filter(function (s) { return s.key === section; })[0];
      if (match) crumb.textContent = match.label;
    }

    // close mobile sidebar
    closeMobileSidebar();
  }

  /* ============ SIDEBAR COLLAPSE / MOBILE ============ */
  function bindSidebar() {
    var collapseBtn = $('collapse-btn');
    var sidebar = $('sidebar');
    var mobileBtn = $('mobile-menu-btn');
    var closeBtn = $('sidebar-close');
    var overlay = $('mobile-overlay');

    if (collapseBtn) {
      collapseBtn.addEventListener('click', function () {
        sidebar.classList.toggle('is-collapsed');
      });
    }

    if (mobileBtn) {
      mobileBtn.addEventListener('click', function () {
        sidebar.classList.add('is-mobile-open');
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', closeMobileSidebar);
    }

    if (overlay) {
      overlay.addEventListener('click', closeMobileSidebar);
    }
  }

  function closeMobileSidebar() {
    var sidebar = $('sidebar');
    if (sidebar) sidebar.classList.remove('is-mobile-open');
  }

  /* ============ DASHBOARD ============ */
  function buildDashboard() {
    // KPI cards
    var kpis = [
      { label: 'Total Users', value: '0', icon: '👤', detail: 'No connected records', color: '' },
      { label: 'Active Users', value: '0', icon: '⏱', detail: 'Awaiting user data', color: 'green' },
      { label: 'Total Chats', value: '0', icon: '✉', detail: 'No chat history yet', color: 'cyan' },
      { label: 'API Requests', value: '0', icon: '⚡', detail: 'No usage recorded', color: 'orange' }
    ];
    var kpiGrid = $('kpi-grid');
    if (kpiGrid) {
      kpiGrid.innerHTML = kpis.map(function (k) {
        return '<div class="kpi-card ' + k.color + '">' +
          '<div class="kpi-icon">' + k.icon + '</div>' +
          '<span>' + k.label + '</span>' +
          '<strong>' + k.value + '</strong>' +
          '<small>' + k.detail + '</small>' +
          '<span class="kpi-arrow">↗</span>' +
          '</div>';
      }).join('');
    }

    // Metric cards
    var metrics = [
      { label: 'Total Tasks', value: '0', detail: 'No tasks recorded', icon: '📋' },
      { label: 'System Uptime', value: '—', detail: 'Connect a monitor', icon: '🕐' },
      { label: 'Storage Usage', value: '—', detail: 'No storage records', icon: '💽' },
      { label: 'Database Size', value: '—', detail: 'No database metrics', icon: '⚙' }
    ];
    var metricsGrid = $('metrics-grid');
    if (metricsGrid) {
      metricsGrid.innerHTML = metrics.map(function (m) {
        return '<div class="metric-card">' +
          '<span class="metric-icon">' + m.icon + '</span>' +
          '<span>' + m.label + '</span>' +
          '<strong>' + m.value + '</strong>' +
          '<small>' + m.detail + '</small>' +
          '</div>';
      }).join('');
    }

    // System status
    var statusList = $('status-list');
    if (statusList) {
      statusList.innerHTML = SYSTEM_SERVICES.map(function (label) {
        return '<div class="status-row"><span>' + label + '</span>' +
          '<strong class="status"><i></i>Not connected</strong></div>';
      }).join('');
    }
  }

  function buildQuickActions() {
    var actions = [
      { label: 'Manage users', section: 'users', icon: '👤' },
      { label: 'View API keys', section: 'keys', icon: '🔑' },
      { label: 'Open terminal', section: 'terminal', icon: '▶_' },
      { label: 'View logs', section: 'logs', icon: '≡' },
      { label: 'Database', section: 'sql', icon: '☡' },
      { label: 'Settings', section: 'theme', icon: '⚙' }
    ];
    var container = $('quick-actions');
    if (container) {
      container.innerHTML = actions.map(function (a) {
        return '<button onclick="switchSection(\'' + a.section + '\')">' +
          '<span class="qa-icon">' + a.icon + '</span>' + a.label +
          '<span class="qa-arrow">›</span></button>';
      }).join('');
    }
  }

  /* ============ USERS ============ */
  function buildRoles() {
    var grid = $('role-grid');
    if (grid) {
      grid.innerHTML = ROLES.map(function (r) {
        return '<div class="role-card ' + r.tone + '">' +
          '<span class="role-icon">⚙</span>' +
          '<div><strong>' + r.role + '</strong><span>' + r.detail + '</span></div>' +
          '<button class="icon-button" onclick="showToast(\'' + r.role + ' permissions are managed by the backend.\')">⋯</button>' +
          '</div>';
      }).join('');
    }

    // Empty users table
    var tbody = $('users-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="7">' +
        '<div class="empty-state">' +
        '<div class="empty-icon">👤</div>' +
        '<strong>No users connected</strong>' +
        '<span>User records will appear here when your identity source is connected.</span>' +
        '<button class="button secondary small" onclick="openModal(\'user\')"><span class="btn-icon">+</span> Add first user</button>' +
        '</div></td></tr>';
    }
  }

  /* ============ API KEYS ============ */
  function buildProviderSelect() {
    var providerSelect = $('provider-select');
    var modelSelect = $('model-select');

    if (providerSelect) {
      providerSelect.innerHTML = Object.keys(MODEL_OPTIONS).map(function (p) {
        return '<option value="' + p + '">' + p + '</option>';
      }).join('');

      providerSelect.addEventListener('change', function () {
        updateModelSelect(providerSelect.value);
      });

      // initialize models
      if (modelSelect) {
        updateModelSelect(providerSelect.value);
      }
    }

    // Empty keys table
    var tbody = $('keys-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="8">' +
        '<div class="empty-state">' +
        '<div class="empty-icon">🔑</div>' +
        '<strong>No API keys connected</strong>' +
        '<span>New provider keys will be masked automatically and never displayed in full.</span>' +
        '<button class="button primary small" onclick="openModal(\'key\')"><span class="btn-icon">+</span> Add a provider</button>' +
        '</div></td></tr>';
    }
  }

  function updateModelSelect(provider) {
    var modelSelect = $('model-select');
    if (!modelSelect) return;
    var models = MODEL_OPTIONS[provider] || [];
    modelSelect.innerHTML = models.map(function (m) {
      return '<option value="' + m + '">' + m + '</option>';
    }).join('');
  }

  /* ============ TERMINAL ============ */
  function bindTerminal() {
    var input = $('terminal-command');
    if (input) {
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') executeCommand();
      });
    }
  }

  window.executeCommand = function () {
    var input = $('terminal-command');
    var body = $('terminal-body');
    if (!input || !body) return;

    var cmd = input.value.trim();
    if (!cmd) return;

    var line = document.createElement('div');
    line.className = 'terminal-line';
    line.innerHTML = '<span class="prompt">admin@shadow:~$</span> ' + escapeHtml(cmd) +
      '<br><span class="muted">Command queued for server authorization.</span>';
    body.appendChild(line);
    body.scrollTop = body.scrollHeight;

    input.value = '';
    showToast('Terminal commands require an authorized server session.');
  };

  window.clearTerminal = function () {
    var body = $('terminal-body');
    if (body) {
      body.innerHTML = '<div class="terminal-line muted">SHADOW OS SECURE TERMINAL</div>' +
        '<div class="terminal-line">Terminal cleared. Awaiting authorized backend connection.</div>';
    }
  };

  /* ============ INBOX ============ */
  function buildInboxTabs() {
    var container = $('inbox-tabs');
    if (!container) return;
    container.innerHTML = INBOX_TABS.map(function (tab) {
      return '<button class="' + (tab === activeInboxTab ? 'active' : '') + '" data-tab="' + tab + '">' +
        tab + '<span class="tab-count">0</span></button>';
    }).join('');

    $$('#inbox-tabs button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        activeInboxTab = btn.getAttribute('data-tab');
        $$('#inbox-tabs button').forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        var title = $('inbox-list-title');
        if (title) title.textContent = activeInboxTab + ' messages';
      });
    });
  }

  /* ============ THEME ============ */
  function buildThemeGrid() {
    var grid = $('theme-grid');
    if (!grid) return;
    grid.innerHTML = THEMES.map(function (t) {
      return '<button class="theme-option" data-theme="' + t.key + '">' +
        '<div class="theme-preview preview-' + t.key + '">' +
        '<div class="preview-top"></div>' +
        '<div class="preview-sidebar"></div>' +
        '<div class="preview-card one"></div>' +
        '<div class="preview-card two"></div>' +
        '<div class="preview-line"></div>' +
        '</div>' +
        '<div class="theme-option-copy">' +
        '<span class="theme-desc">' + t.desc + '</span>' +
        '<strong>' + t.label + '</strong>' +
        '<span class="theme-check">✓</span>' +
        '</div>' +
        '</button>';
    }).join('');

    $$('.theme-option').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var key = btn.getAttribute('data-theme');
        applyTheme(key);
      });
    });
  }

  function applyTheme(key) {
    document.documentElement.setAttribute('data-theme', key);
    localStorage.setItem('shadow-theme', key);

    $$('.theme-option').forEach(function (btn) {
      btn.classList.toggle('selected', btn.getAttribute('data-theme') === key);
    });
  }

  function restoreTheme() {
    var saved = localStorage.getItem('shadow-theme') || 'blue';
    applyTheme(saved);
  }

  /* ============ SQL ============ */
  window.runSql = function () {
    var query = $('sql-query');
    var status = $('sql-result-status');
    if (!query) return;

    if (query.value.trim()) {
      if (status) status.textContent = 'Awaiting authorization';
    } else {
      if (status) status.textContent = 'No query executed';
    }
    showToast('SQL queries require an authorized backend session.');
  };

  /* ============ LOGS ============ */
  function buildLogTabs() {
    var container = $('log-tabs');
    if (!container) return;
    container.innerHTML = LOG_TABS.map(function (tab) {
      return '<button class="' + (tab === activeLogTab ? 'active' : '') + '" data-tab="' + tab + '">' + tab + '</button>';
    }).join('');

    $$('#log-tabs button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        activeLogTab = btn.getAttribute('data-tab');
        $$('#log-tabs button').forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        var title = $('logs-title');
        if (title) title.textContent = activeLogTab;
      });
    });

    // Empty logs table
    var tbody = $('logs-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="5">' +
        '<div class="empty-state">' +
        '<div class="empty-icon">≡</div>' +
        '<strong>No logs found</strong>' +
        '<span>Events will appear here as connected services begin reporting activity.</span>' +
        '</div></td></tr>';
    }
  }

  /* ============ SEARCH ============ */
  function bindSearch() {
    var userSearch = $('user-search');
    if (userSearch) {
      userSearch.addEventListener('input', function () {
        var q = userSearch.value.trim();
        var count = $('users-count');
        if (count) count.textContent = q ? '0 users match' : '0 users';
      });
    }

    var logSearch = $('log-search');
    if (logSearch) {
      logSearch.addEventListener('input', function () {
        var q = logSearch.value.trim();
        var count = $('logs-count');
        if (count) count.textContent = q ? '0 matching records' : '0 log records';
      });
    }
  }

  /* ============ TOAST ============ */
  window.showToast = function (message) {
    var toast = $('toast');
    if (!toast) return;
    toast.innerHTML = '<span class="toast-icon">✓</span>' + escapeHtml(message);
    toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toast.classList.remove('show');
    }, 3200);
  };

  /* ============ MODAL ============ */
  function bindModal() {
    var backdrop = $('modal-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) closeModal();
      });
    }
  }

  window.openModal = function (kind) {
    var backdrop = $('modal-backdrop');
    var content = $('modal-content');
    if (!backdrop || !content) return;

    var isUser = kind === 'user';

    content.innerHTML =
      '<div class="modal-heading">' +
      '<div><div class="eyebrow"><span></span>SECURE ACTION</div>' +
      '<h2>' + (isUser ? 'Add user' : 'Add API key') + '</h2></div>' +
      '<button class="icon-button" onclick="closeModal()">✕</button>' +
      '</div>' +
      '<p>' + (isUser
        ? 'Create a directory record for an authorized account.'
        : 'Connect a provider without exposing the secret in the interface.') + '</p>' +
      '<div class="form-stack">' +
      (isUser
        ? '<label>Username<input placeholder="e.g. operator" /></label>' +
        '<label>Email<input type="email" placeholder="operator@shadow.os" /></label>' +
        '<label>Access role<select><option>Admin</option><option>Sub Admin</option><option>User</option><option>Guest</option></select></label>'
        : '<label>Provider<select id="modal-provider">' + Object.keys(MODEL_OPTIONS).map(function (p) { return '<option>' + p + '</option>'; }).join('') + '</select></label>' +
        '<label>Key name<input placeholder="Production key" /></label>' +
        '<label>API key<input type="password" placeholder="Secret is never displayed" /></label>'
      ) +
      '<div class="form-hint"><span class="hint-icon">🔒</span> This action will be validated by the protected backend.</div>' +
      '</div>' +
      '<div class="modal-actions">' +
      '<button class="button secondary" onclick="closeModal()">Cancel</button>' +
      '<button class="button primary" onclick="confirmModal(\'' + kind + '\')"><span class="btn-icon">🛡</span> Continue securely</button>' +
      '</div>';

    backdrop.classList.add('show');
  };

  window.confirmModal = function (kind) {
    var label = kind === 'user' ? 'User' : 'API key';
    showToast(label + ' creation requires an authorized backend session.');
    closeModal();
  };

  window.closeModal = function () {
    var backdrop = $('modal-backdrop');
    if (backdrop) backdrop.classList.remove('show');
  };

  /* ============ UTIL ============ */
  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  /* ============ EXPOSE switchSection for inline onclick ============ */
  window.switchSection = switchSection;

  /* ============ LAUNCH ============ */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

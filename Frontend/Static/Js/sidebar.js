/**
 * SHADOW OS — Shared Sidebar, Top Navbar & Navigation System
 * Top Navbar (Search, Notifications, Network, Settings) + Left Sidebar + Session Profile
 */

(function () {
  "use strict";

  const SIDEBAR_STORAGE_KEY = "shadow_sidebar_collapsed";

  document.addEventListener("DOMContentLoaded", () => {
    initTopNavbarSearch();
    initTopNavbarDropdowns();
    initNetworkMonitor();
    initSidebar();
    initMobileDrawer();
    initActiveNav();
    initHeaderClock();
    initSessionStatus();
    initAdminShortcut();
  });

  function applyRoleAwareNav(isAdmin) {
    const nav = document.querySelector(".sidebar-nav"); if (nav && nav.dataset.noAutoNav) return;
    if (!nav) return;

    const dataLink = nav.querySelector('a[href="/data"]');
    if (isAdmin && !dataLink) {
      const dataItem = document.createElement("a");
      dataItem.href = "/data";
      dataItem.className = "nav-item";
      dataItem.dataset.tooltip = "Data Vault";
      dataItem.innerHTML = `
        <div class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v11A2.5 2.5 0 0 1 17.5 20h-11A2.5 2.5 0 0 1 4 17.5v-11z"></path>
            <path d="M8 8h8M8 12h8M8 16h5"></path>
          </svg>
        </div>
        <span class="nav-label">Data</span>
      `;
      nav.appendChild(dataItem);
    }

    const adminLink = nav.querySelector('a[href="/admin"]');
    if (isAdmin && !adminLink) {
      const adminItem = document.createElement("a");
      adminItem.href = "/admin";
      adminItem.className = "nav-item";
      adminItem.dataset.tooltip = "Admin Panel";
      adminItem.innerHTML = `
        <div class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v7"></path>
            <path d="M12 15v7"></path>
            <path d="M4.93 4.93l4.95 4.95"></path>
            <path d="M14.12 14.12l4.95 4.95"></path>
            <path d="M2 12h7"></path>
            <path d="M15 12h7"></path>
            <path d="M4.93 19.07l4.95-4.95"></path>
            <path d="M14.12 9.88l4.95-4.95"></path>
          </svg>
        </div>
        <span class="nav-label">Admin Panel</span>
      `;
      nav.appendChild(adminItem);
    } else if (!isAdmin && adminLink) {
      adminLink.remove();
    }

    initActiveNav();
  }

  /* --------------------------------------------------------------------------
     1. GLOBAL TOP NAVBAR SEARCH
     -------------------------------------------------------------------------- */
  function initTopNavbarSearch() {
    const searchInput = document.getElementById("globalSearchInput");
    const dropdown = document.getElementById("searchResultsDropdown");
    if (!searchInput || !dropdown) return;

    const searchableItems = [
      { title: "Dashboard", url: "/dashboard", cat: "WORKSPACE", desc: "Main telemetry & AI HUD" },
      { title: "AI Chatbot", url: "/ai-chatbot", cat: "NEURAL", desc: "SHADOWconversational agent" },
      { title: "Image Studio", url: "/image", cat: "STUDIO", desc: "Neural artwork synthesizer" },
      { title: "Sketch Studio", url: "/sketch", cat: "STUDIO", desc: "AI contour animator & canvas" },
      { title: "Music Player", url: "/music", cat: "MEDIA", desc: "Cyber audio player & queue" },
      { title: "Neural Files", url: "/files", cat: "DATA", desc: "Categorized project vault" },
      { title: "API Keys", url: "/api-keys", cat: "SYSTEM", desc: "Neural engine credentials" },
      { title: "Upgrade Tiers", url: "/upgrade", cat: "SYSTEM", desc: "Hardware & model tiers" },
      { title: "Operator Profile", url: "/profile", cat: "SYSTEM", desc: "Account & security matrix" }
    ];

    searchInput.addEventListener("input", () => {
      const q = searchInput.value.trim().toLowerCase();
      if (!q) {
        dropdown.style.display = "none";
        dropdown.innerHTML = "";
        return;
      }

      const matches = searchableItems.filter(item => 
        item.title.toLowerCase().includes(q) || 
        item.cat.toLowerCase().includes(q) || 
        item.desc.toLowerCase().includes(q)
      );

      if (matches.length === 0) {
        dropdown.innerHTML = `<div style="padding: 12px; text-align: center; color: var(--text-muted); font-size: 0.75rem; font-family: var(--font-mono);">NO NEURAL MATCHES FOUND</div>`;
      } else {
        dropdown.innerHTML = matches.map(m => `
          <a href="${m.url}" class="search-result-item">
            <svg class="search-result-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 14 14"></polyline>
            </svg>
            <div>
              <div style="font-weight: 700;">${m.title}</div>
              <div style="font-size: 0.68rem; color: var(--text-muted);">${m.desc}</div>
            </div>
            <span class="search-result-category">${m.cat}</span>
          </a>
        `).join("");
      }

      dropdown.style.display = "block";
    });

    // Close search dropdown on click outside
    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });

    // Handle Enter key
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const firstMatch = dropdown.querySelector(".search-result-item");
        if (firstMatch) {
          window.location.href = firstMatch.getAttribute("href");
        }
      }
    });
  }

  /* --------------------------------------------------------------------------
     2. NOTIFICATIONS & SETTINGS DROPDOWNS
     -------------------------------------------------------------------------- */
  function initTopNavbarDropdowns() {
    const notifBtn = document.getElementById("navNotifBtn");
    const notifDropdown = document.getElementById("notifDropdown");
    const settingsBtn = document.getElementById("navSettingsBtn");
    const settingsDropdown = document.getElementById("settingsDropdown");
    const clearNotifBtn = document.getElementById("clearNotifBtn");
    const notifBadge = document.getElementById("notifBadge");
    const navLogoutBtn = document.getElementById("navLogoutBtn");

    if (notifBtn && notifDropdown) {
      notifBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = notifDropdown.style.display === "block";
        if (settingsDropdown) settingsDropdown.style.display = "none";
        notifDropdown.style.display = isOpen ? "none" : "block";
      });
    }

    if (clearNotifBtn) {
      clearNotifBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const notifList = document.getElementById("notifList");
        if (notifList) {
          notifList.innerHTML = `<div style="padding: 14px; text-align: center; color: var(--text-muted); font-size: 0.72rem; font-family: var(--font-mono);">LOGS CLEARED</div>`;
        }
        if (notifBadge) notifBadge.style.display = "none";
      });
    }

    if (settingsBtn && settingsDropdown) {
      settingsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = settingsDropdown.style.display === "block";
        if (notifDropdown) notifDropdown.style.display = "none";
        settingsDropdown.style.display = isOpen ? "none" : "block";
      });
    }

    if (navLogoutBtn) {
      navLogoutBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        try {
          const res = await fetch("/api/logout", { method: "POST" });
          const data = await res.json().catch(() => ({}));
          window.location.href = data.redirect || "/login";
        } catch {
          window.location.href = "/login";
        }
      });
    }

    // Close on click outside
    document.addEventListener("click", () => {
      if (notifDropdown) notifDropdown.style.display = "none";
      if (settingsDropdown) settingsDropdown.style.display = "none";
    });
  }

  /* --------------------------------------------------------------------------
     3. DYNAMIC NETWORK TELEMETRY MONITOR
     -------------------------------------------------------------------------- */
  function initNetworkMonitor() {
    const indicator = document.getElementById("navNetworkStatus");
    const label = document.getElementById("navNetworkLabel");
    if (!indicator || !label) return;

    function updateNetworkStatus(online) {
      if (online) {
        indicator.classList.remove("offline");
        label.textContent = "ONLINE";
      } else {
        indicator.classList.add("offline");
        label.textContent = "OFFLINE";
      }
      // Broadcast to any page listener
      window.dispatchEvent(new CustomEvent("shadow-network-change", { detail: { online } }));
    }

    updateNetworkStatus(navigator.onLine);

    window.addEventListener("online", () => {
      updateNetworkStatus(true);
      if (window.showCyberToast) window.showCyberToast("Network connection established", "success");
    });

    window.addEventListener("offline", () => {
      updateNetworkStatus(false);
      if (window.showCyberToast) window.showCyberToast("Network offline — operating in local mode", "error");
    });

    // Check with server endpoint periodically
    async function checkServerPing() {
      try {
        const res = await fetch("/status", { cache: "no-store" });
        updateNetworkStatus(res.ok);
      } catch {
        updateNetworkStatus(false);
      }
    }

    setInterval(checkServerPing, 10000);
  }

  /* --------------------------------------------------------------------------
     4. SIDEBAR COLLAPSE & EXPAND LOGIC
     -------------------------------------------------------------------------- */
  function initSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const toggleBtn = document.getElementById("sidebarToggleBtn");
    if (!sidebar || !toggleBtn) return;

    // Restore user preference
    const isCollapsed = localStorage.getItem(SIDEBAR_STORAGE_KEY) === "true";
    if (isCollapsed && window.innerWidth > 768) {
      sidebar.classList.add("collapsed");
    }

    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      const currentState = sidebar.classList.contains("collapsed");
      localStorage.setItem(SIDEBAR_STORAGE_KEY, currentState);
      window.dispatchEvent(new Event("resize"));
    });

    // Keyboard shortcut: Ctrl + B or Alt + S
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey && e.key.toLowerCase() === "b") || (e.altKey && e.key.toLowerCase() === "s")) {
        e.preventDefault();
        sidebar.classList.toggle("collapsed");
        localStorage.setItem(SIDEBAR_STORAGE_KEY, sidebar.classList.contains("collapsed"));
        window.dispatchEvent(new Event("resize"));
      }
    });
  }

  /* --------------------------------------------------------------------------
     5. MOBILE DRAWER NAVIGATION
     -------------------------------------------------------------------------- */
  function initMobileDrawer() {
    const sidebar = document.querySelector(".sidebar");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const closeBtn = document.getElementById("mobileSidebarClose");
    const backdrop = document.getElementById("mobileBackdrop");

    if (!sidebar) return;

    function openDrawer() {
      sidebar.classList.add("mobile-open");
      if (backdrop) backdrop.classList.add("active");
      document.body.style.overflow = "hidden";
    }

    function closeDrawer() {
      sidebar.classList.remove("mobile-open");
      if (backdrop) backdrop.classList.remove("active");
      document.body.style.overflow = "";
    }

    if (mobileMenuBtn) {
      mobileMenuBtn.addEventListener("click", openDrawer);
    }

    if (closeBtn) {
      closeBtn.addEventListener("click", closeDrawer);
    }

    if (backdrop) {
      backdrop.addEventListener("click", closeDrawer);
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sidebar.classList.contains("mobile-open")) {
        closeDrawer();
      }
    });

    sidebar.querySelectorAll(".nav-item").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
          closeDrawer();
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     6. ACTIVE NAVIGATION LINK DETECTION
     -------------------------------------------------------------------------- */
  function initActiveNav() {
    const currentPath = window.location.pathname.toLowerCase();
    const navItems = document.querySelectorAll(".sidebar .nav-item");

    navItems.forEach((item) => {
      const href = (item.getAttribute("href") || "").toLowerCase();
      if (!href) return;

      if (
        currentPath === href ||
        (href === "/dashboard" && (currentPath === "/index" || currentPath === "/app" || currentPath === "/")) ||
        (href === "/ai-chatbot" && currentPath === "/chatbot") ||
        (href === "/data" && currentPath === "/data") ||
        (href === "/admin" && currentPath === "/admin")
      ) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });
  }

  /* --------------------------------------------------------------------------
     7. LIVE UTC & LOCAL CLOCK
     -------------------------------------------------------------------------- */
  function initHeaderClock() {
    const clockEl = document.getElementById("headerClock");
    if (!clockEl) return;

    function updateClock() {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      const seconds = String(now.getSeconds()).padStart(2, "0");
      clockEl.textContent = `${hours}:${minutes}:${seconds} UTC`;
    }

    updateClock();
    setInterval(updateClock, 1000);
  }

  /* --------------------------------------------------------------------------
     8. USER SESSION STATUS & SIDEBAR PROFILE (REAL DATA, NO HARDCODING)
     -------------------------------------------------------------------------- */
  async function initSessionStatus() {
    const nameEl = document.getElementById("operatorName");
    const emailEl = document.getElementById("operatorEmail");
    const roleEl = document.getElementById("operatorRole");

    try {
      const res = await fetch("/api/session-status");
      const data = await res.json();

      if (!data.logged_in) {
        const publicPages = ["/loading", "/login", "/signup", "/forgot-password", "/otp"];
        const currentPath = window.location.pathname;
        if (!publicPages.includes(currentPath)) {
          window.location.href = "/login";
        }
        return;
      }

      const username = data.username || "Operator";
      const email = data.email || `${username.toLowerCase()}@shadow.os`;
      const role = data.role ? data.role.toUpperCase() : "ACTIVE";
      const isAdmin = Boolean(data.is_admin || role === "ADMIN");

      if (nameEl) nameEl.textContent = username;
      if (emailEl) emailEl.textContent = email;
      if (roleEl) roleEl.textContent = role;

      applyRoleAwareNav(isAdmin);

      // Broadcast user identity for other modules
      window.currentUser = { username, email, role, is_admin: isAdmin };
      window.dispatchEvent(new CustomEvent("shadow-user-loaded", { detail: window.currentUser }));

    } catch (err) {
      console.warn("Session status check error:", err);
    }
  }

  /* --------------------------------------------------------------------------
     9. GLOBAL CYBER TOAST HELPER
     -------------------------------------------------------------------------- */
  window.showCyberToast = function (message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconSvg = "";
    if (type === "success") {
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    } else if (type === "error") {
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    } else {
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
    }

    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  };
  function initAdminShortcut() {
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.altKey && e.key.toLowerCase() === "a") {
        e.preventDefault();
        if (window.currentUser && window.currentUser.is_admin) {
          window.location.href = "/admin";
        } else {
          console.warn("Admin panel access denied.");
        }
      }
    });
  }

})();

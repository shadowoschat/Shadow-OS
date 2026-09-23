/**
 * SHADOW OS — Operator Profile Controller
 * Loads session info from /api/session-status, device.json, and security toggles
 */

(function () {
  "use strict";

  /* ── Session Info ───────────────────────────────────────────────────── */
  async function loadSession() {
    try {
      const res  = await fetch("/api/session-status");
      const data = await res.json();

      if (!data.logged_in) {
        window.location.href = "/login";
        return;
      }

      set("profileOperatorName", data.username || "Operator");
      set("profileRole", "OPERATOR CORE");
      set("sessionUsername", data.username || "—");
      set("sessionIP", data.ip || navigator.language || "—");
      set("sessionSince", new Date().toLocaleDateString());
      set("sessionAgent", navigator.userAgent.split(" ")[0] || "—");

      // Also update sidebar name
      const sidebarName = document.getElementById("operatorName");
      if (sidebarName) sidebarName.textContent = data.username || "Operator";
    } catch (e) {
      console.warn("Session fetch failed:", e);
    }
  }

  /* ── Devices ─────────────────────────────────────────────────────────── */
  function loadDevices() {
    const list = document.getElementById("deviceList");
    if (!list) return;

    // Static device list (device.json not served via API, show sensible defaults)
    const devices = [
      { name: "Current Browser",   meta: navigator.userAgent.split(")")[0].split("(")[1] || "Unknown", current: true },
      { name: "Terminal Session",  meta: "Local OS Process",                                             current: false },
    ];

    list.innerHTML = devices.map(d => `
      <div class="device-item">
        <div>
          <div class="device-name">${d.name} ${d.current ? '<span class="cyber-badge" style="font-size:0.65rem;padding:2px 8px;">CURRENT</span>' : ""}</div>
          <div class="device-meta">${d.meta}</div>
        </div>
        ${!d.current ? `<button class="btn-cyber btn-cyber-danger" style="padding:5px 12px;font-size:0.72rem;">REVOKE</button>` : ""}
      </div>
    `).join("");
  }

  /* ── Logout ─────────────────────────────────────────────────────────── */
  document.getElementById("profileLogoutBtn")?.addEventListener("click", async () => {
    try {
      await fetch("/api/logout", { method: "POST" });
    } finally {
      window.location.href = "/login";
    }
  });

  /* ── Helper ─────────────────────────────────────────────────────────── */
  function set(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  /* ── Init ───────────────────────────────────────────────────────────── */
  loadSession();
  loadDevices();
})();

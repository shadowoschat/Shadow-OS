/**
 * SHADOW OS — API Keys Manager Controller
 * Reads /api/get-env, reveals masked keys, validates admin password, updates /api/update-env
 */

(function () {
  "use strict";

  

  const KEY_DEFS = [
    { envKey: "COHERE_API_KEY",       label: "Cohere AI",         desc: "Language model & chat engine",            icon: "🔮", color: "#7b2fff" },
    { envKey: "GROQ_API_KEY",         label: "Groq LLM",          desc: "Ultra-fast inference engine",             icon: "⚡", color: "#ffd700" },
    { envKey: "HUGGINGFACE_API_KEY",  label: "HuggingFace",       desc: "Image & ML model hub",                    icon: "🤗", color: "#ff6b35" },
    { envKey: "InputLanguage",        label: "Input Language",    desc: "en, hi, or mr for voice selection",       icon: "🌐", color: "#00ff80" },
    { envKey: "ASSISTANT_VOICE",      label: "Assistant Voice",   desc: "Edge-TTS voice: en-IN-NeerjaNeural / hi-IN-SwaraNeural / mr-IN-AarohiNeural", icon: "🎙", color: "var(--cyan)" },
    { envKey: "USERNAME",             label: "Operator Username", desc: "Shadow OS operator identity",             icon: "👤", color: "#00ff80" }
  ];

  let envData      = {};
  let pendingEdit  = null; // { envKey, inputEl }

  /* ── Load current env values ──────────────────────────────────────────── */
  async function loadEnv() {
    try {
      const res = await fetch("/api/get-env");
      envData   = await res.json();
    } catch (e) {
      envData = {};
    }
    renderCards();
  }

  /* ── Render key cards ─────────────────────────────────────────────────── */
  function renderCards() {
    const grid = document.getElementById("apiKeysGrid");
    if (!grid) return;
    grid.innerHTML = "";

    KEY_DEFS.forEach(def => {
      const rawVal   = envData[def.envKey] || "";
      const maskedVal = rawVal ? maskValue(rawVal) : "— NOT SET —";

      const card = document.createElement("div");
      card.className = "api-key-card";
      card.id = `card-${def.envKey}`;
      card.innerHTML = `
        <div class="api-key-service">
          <div class="api-key-service-icon" style="background:rgba(${hexToRgb(def.color) || "0,234,255"},0.12);color:${def.color};">${def.icon}</div>
          <div>
            <div class="api-key-service-name">${def.label}</div>
            <div class="api-key-service-desc">${def.desc}</div>
          </div>
        </div>

        <div class="api-key-field-wrap">
          <input class="api-key-input" id="input-${def.envKey}" type="text" readonly value="${maskedVal}" />
          <button class="icon-btn" id="reveal-${def.envKey}" title="Reveal / Hide" data-key="${def.envKey}" data-revealed="false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
          <button class="icon-btn" id="edit-${def.envKey}" title="Edit Key" data-key="${def.envKey}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          </button>
        </div>

        <div class="api-key-footer">
          <span class="cyber-badge ${rawVal ? "" : "badge-danger"}">${rawVal ? "CONFIGURED" : "MISSING"}</span>
          <span style="font-family:var(--font-mono);font-size:0.72rem;color:var(--text-muted);">ENV: ${def.envKey}</span>
        </div>
      `;

      // Reveal button
      card.querySelector(`#reveal-${def.envKey}`)?.addEventListener("click", (e) => {
        const btn     = e.currentTarget;
        const inputEl = document.getElementById(`input-${def.envKey}`);
        const isRevealed = btn.dataset.revealed === "true";
        btn.dataset.revealed = (!isRevealed).toString();
        if (inputEl) inputEl.value = isRevealed ? maskedVal : (rawVal || "— NOT SET —");
      });

      // Edit button
      card.querySelector(`#edit-${def.envKey}`)?.addEventListener("click", () => {
        pendingEdit = { envKey: def.envKey, inputEl: document.getElementById(`input-${def.envKey}`) };
        openAuthModal();
      });

      grid.appendChild(card);
    });
  }

  /* ── Auth Modal ─────────────────────────────────────────────────────────── */
  function openAuthModal() {
    document.getElementById("authPasswordInput").value = "";
    document.getElementById("authModal")?.classList.add("active");
    document.getElementById("authPasswordInput")?.focus();
  }

  function closeAuthModal() {
    document.getElementById("authModal")?.classList.remove("active");
  }

  document.getElementById("authCancelBtn")?.addEventListener("click", closeAuthModal);

  document.getElementById("authConfirmBtn")?.addEventListener("click", () => {
    
    closeAuthModal();
    // Enable editing the pending input
    if (pendingEdit?.inputEl) {
      const input = pendingEdit.inputEl;
      const rawVal = envData[pendingEdit.envKey] || "";
      input.value = rawVal;
      input.readOnly = false;
      input.classList.add("editable");
      input.focus();

      // Save on Enter or blur
      const saveKey = async () => {
        const newVal = input.value.trim();
        input.readOnly = true;
        input.classList.remove("editable");
        if (newVal === (envData[pendingEdit.envKey] || "")) return;
        try {
          const res = await fetch("/api/update-env", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: pendingEdit.envKey, value: newVal })
          });
          const data = await res.json().catch(() => ({}));
          if (window.showCyberToast) window.showCyberToast(data.message || "Key updated", "success");
          envData[pendingEdit.envKey] = newVal;
          renderCards();
        } catch (e) {
          if (window.showCyberToast) window.showCyberToast("Failed to save key", "error");
        }
      };

      input.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); saveKey(); } }, { once: true });
      input.addEventListener("blur", saveKey, { once: true });
    }
  });

  /* ── Helpers ────────────────────────────────────────────────────────────── */
  function maskValue(val) {
    if (!val || val.length < 6) return "••••••";
    return val.substring(0, 4) + "•".repeat(Math.max(val.length - 8, 4)) + val.slice(-4);
  }

  function hexToRgb(hex) {
    if (!hex || hex.startsWith("var")) return "0,234,255";
    const h = hex.replace("#", "");
    const n = parseInt(h, 16);
    return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
  }

  /* ── Init ───────────────────────────────────────────────────────────── */
  loadEnv();
})();

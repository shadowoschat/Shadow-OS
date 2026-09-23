/**
 * SHADOW OS — Files Explorer Controller
 * Lists files from /api/files-list, category filtering, search, and preview modal
 */

(function () {
  "use strict";

  let allFiles   = [];
  let activeCategory = "all";

  const ICONS = {
    audio:  { emoji: "🎵", bg: "rgba(123,47,255,0.15)", color: "#7b2fff" },
    image:  { emoji: "🖼",  bg: "rgba(0,234,255,0.12)", color: "var(--cyan)" },
    data:   { emoji: "📄",  bg: "rgba(255,204,0,0.1)",  color: "#ffd700" },
    system: { emoji: "⚙",  bg: "rgba(0,255,128,0.1)",  color: "#00ff80" },
    other:  { emoji: "📁",  bg: "rgba(255,255,255,0.06)", color: "#aaa" }
  };

  function categorize(name) {
    const ext = (name.split(".").pop() || "").toLowerCase();
    if (["mp3", "wav", "ogg", "flac"].includes(ext)) return "audio";
    if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(ext)) return "image";
    if (["json", "txt", "csv", "md", "log", "data"].includes(ext)) return "data";
    if (["py", "js", "sh", "bat"].includes(ext)) return "system";
    return "other";
  }

  async function loadFiles() {
    const grid = document.getElementById("filesGrid");
    if (!grid) return;
    grid.innerHTML = `<p style="color:var(--text-muted);font-family:var(--font-mono);font-size:0.8rem;padding:20px;">Loading data matrix...</p>`;

    try {
      const res   = await fetch("/api/files-list");
      allFiles    = await res.json();
      renderFiles();
      updateStorageStats();
    } catch (e) {
      grid.innerHTML = `<p style="color:#ff4d6a;font-size:0.8rem;font-family:var(--font-mono);">Failed to load files: ${e.message}</p>`;
    }
  }

  function renderFiles() {
    const grid       = document.getElementById("filesGrid");
    const query      = (document.getElementById("filesSearchInput")?.value || "").toLowerCase();
    if (!grid) return;

    const filtered = allFiles.filter(f => {
      const cat = categorize(f.name);
      if (activeCategory !== "all" && cat !== activeCategory) return false;
      if (query && !f.name.toLowerCase().includes(query)) return false;
      return true;
    });

    if (filtered.length === 0) {
      grid.innerHTML = `<p style="grid-column:1/-1;color:var(--text-muted);font-family:var(--font-mono);font-size:0.8rem;padding:20px;">No files match the current filter.</p>`;
      return;
    }

    grid.innerHTML = "";
    filtered.forEach(f => {
      const cat  = categorize(f.name);
      const icon = ICONS[cat] || ICONS.other;
      const card = document.createElement("div");
      card.className = "file-card";
      card.innerHTML = `
        <div class="file-icon-wrap" style="background:${icon.bg};color:${icon.color};">${icon.emoji}</div>
        <div class="file-card-name">${f.name}</div>
        <div class="file-card-meta">${f.size || ""} &bull; ${cat.toUpperCase()}</div>
      `;
      card.title = f.path || f.name;
      grid.appendChild(card);
    });
  }

  function updateStorageStats() {
    const counts = { audio: 0, image: 0, data: 0, system: 0 };
    allFiles.forEach(f => {
      const cat = categorize(f.name);
      if (counts[cat] !== undefined) counts[cat]++;
    });

    const sets = [
      { id: "statAudio", val: counts.audio },
      { id: "statImage", val: counts.image },
      { id: "statData",  val: counts.data  },
      { id: "statTotal", val: allFiles.length }
    ];

    sets.forEach(({ id, val }) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    });

    // Storage fill placeholder (we don't have byte info, simulate)
    const fill = document.getElementById("storageGaugeFill");
    const pct  = Math.min(allFiles.length * 3, 85);
    if (fill) fill.style.width = pct + "%";
    const used = document.getElementById("storageUsed");
    if (used) used.textContent = pct + "%";
  }

  /* ── Category chips ─────────────────────────────────────────────────── */
  document.querySelectorAll(".cat-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".cat-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeCategory = chip.dataset.cat || "all";
      renderFiles();
    });
  });

  /* ── Search ─────────────────────────────────────────────────────────── */
  document.getElementById("filesSearchInput")?.addEventListener("input", renderFiles);

  /* ── Init ───────────────────────────────────────────────────────────── */
  loadFiles();
})();

/**
 * SHADOW OS — Sketch Studio Controller
 * Tab 1: Interactive freehand drawing canvas (brush size, color, undo, save)
 * Tab 2: AI Contour Animator using /api/chat (draw_sketch) + pencil sound
 */

(function () {
  "use strict";

  /* ── Tab switching ────────────────────────────────────────────────────── */
  const tabs = {
    draw:    { btn: "tabDrawBtn",     panel: "drawPanel"     },
    animate: { btn: "tabAnimateBtn",  panel: "animatePanel"  }
  };

  function switchTab(active) {
    Object.entries(tabs).forEach(([key, { btn, panel }]) => {
      const b = document.getElementById(btn);
      const p = document.getElementById(panel);
      if (key === active) {
        b?.classList.add("active");
        if (p) p.style.display = "";
      } else {
        b?.classList.remove("active");
        if (p) p.style.display = "none";
      }
    });
  }

  document.getElementById("tabDrawBtn")?.addEventListener("click", () => switchTab("draw"));
  document.getElementById("tabAnimateBtn")?.addEventListener("click", () => {
    switchTab("animate");
    loadRefImages();
  });

  /* ════════════════════════════════════════════════════════════════════════
     TAB 1 — INTERACTIVE DRAWING CANVAS
  ═════════════════════════════════════════════════════════════════════════ */
  const canvas  = document.getElementById("drawCanvas");
  const ctx     = canvas?.getContext("2d");
  let painting  = false;
  let history   = [];
  let histIndex = -1;

  function saveSnapshot() {
    if (!ctx || !canvas) return;
    history = history.slice(0, histIndex + 1);
    history.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
    histIndex = history.length - 1;
  }

  function resizeCanvas() {
    if (!canvas) return;
    const wrap = canvas.parentElement;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    const saved = ctx.getImageData(0, 0, canvas.width, canvas.height);
    canvas.width  = w;
    canvas.height = h;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
    ctx.putImageData(saved, 0, 0);
    applyToolSettings();
  }

  function applyToolSettings() {
    if (!ctx) return;
    const brushColor = document.getElementById("brushColorPicker")?.value || "#000000";
    const brushSize  = document.getElementById("brushSizeRange")?.value  || 5;
    const eraserMode = document.getElementById("eraserBtn")?.classList.contains("active");
    ctx.lineWidth   = eraserMode ? 24 : brushSize;
    ctx.strokeStyle = eraserMode ? "#ffffff" : brushColor;
    ctx.lineCap     = "round";
    ctx.lineJoin    = "round";
  }

  function getPos(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width  / rect.width;
    const scaleY = canvas.height / rect.height;
    const touch  = e.touches?.[0] || e;
    return {
      x: (touch.clientX - rect.left) * scaleX,
      y: (touch.clientY - rect.top)  * scaleY
    };
  }

  function startDraw(e) {
    painting = true;
    saveSnapshot();
    applyToolSettings();
    ctx.beginPath();
    const { x, y } = getPos(e);
    ctx.moveTo(x, y);
  }

  function draw(e) {
    if (!painting) return;
    e.preventDefault();
    const { x, y } = getPos(e);
    ctx.lineTo(x, y);
    ctx.stroke();
  }

  function stopDraw() {
    painting = false;
    ctx?.beginPath();
  }

  if (canvas) {
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    canvas.addEventListener("mousedown",  startDraw);
    canvas.addEventListener("mousemove",  draw);
    canvas.addEventListener("mouseup",    stopDraw);
    canvas.addEventListener("mouseleave", stopDraw);
    canvas.addEventListener("touchstart", startDraw, { passive: false });
    canvas.addEventListener("touchmove",  draw,      { passive: false });
    canvas.addEventListener("touchend",   stopDraw);

    document.getElementById("brushColorPicker")?.addEventListener("input",  applyToolSettings);
    document.getElementById("brushSizeRange")?.addEventListener("input",    applyToolSettings);
    document.getElementById("brushSizeLabel") && (() => {
      const range = document.getElementById("brushSizeRange");
      const label = document.getElementById("brushSizeLabel");
      range?.addEventListener("input", () => { label.textContent = range.value + "px"; });
    })();

    document.getElementById("eraserBtn")?.addEventListener("click", function () {
      this.classList.toggle("active");
      applyToolSettings();
    });

    document.getElementById("clearBtn")?.addEventListener("click", () => {
      saveSnapshot();
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    });

    document.getElementById("undoBtn")?.addEventListener("click", () => {
      if (histIndex > 0) {
        histIndex--;
        ctx.putImageData(history[histIndex], 0, 0);
      }
    });

    document.getElementById("saveDrawingBtn")?.addEventListener("click", () => {
      const link = document.createElement("a");
      link.href     = canvas.toDataURL("image/png");
      link.download = `shadow-sketch-${Date.now()}.png`;
      link.click();
    });
  }

  /* ════════════════════════════════════════════════════════════════════════
     TAB 2 — AI CONTOUR ANIMATOR
  ═════════════════════════════════════════════════════════════════════════ */
  let selectedRefImage = null;

  async function loadRefImages() {
    const grid = document.getElementById("refImageGrid");
    if (!grid) return;
    grid.innerHTML = `<p style="color:var(--text-muted);font-size:0.8rem;">Loading reference images...</p>`;

    try {
      const res  = await fetch("/api/images");
      const imgs = await res.json();

      if (!imgs || imgs.length === 0) {
        grid.innerHTML = `<p style="color:var(--text-muted);font-size:0.8rem;">No reference images found. Generate some in the Image Studio first!</p>`;
        return;
      }

      grid.innerHTML = "";
      imgs.forEach((img) => {
        const el = document.createElement("div");
        el.className = "ref-image-thumb";
        el.innerHTML = `<img src="${img.url}" alt="${img.name}" style="width:100%;height:80px;object-fit:cover;border-radius:6px;cursor:pointer;border:2px solid transparent;" />`;
        el.querySelector("img").addEventListener("click", () => {
          document.querySelectorAll(".ref-image-thumb img").forEach(i => i.style.borderColor = "transparent");
          el.querySelector("img").style.borderColor = "var(--cyan)";
          selectedRefImage = img;
          const preview = document.getElementById("refImagePreview");
          if (preview) preview.src = img.url;
          const nameEl = document.getElementById("refImageName");
          if (nameEl) nameEl.textContent = img.name;
        });
        grid.appendChild(el);
      });
    } catch (err) {
      grid.innerHTML = `<p style="color:#ff4d6a;font-size:0.8rem;">Failed to load images: ${err.message}</p>`;
    }
  }

  document.getElementById("runSketchBtn")?.addEventListener("click", async () => {
    const imgNameInput = document.getElementById("sketchImageNameInput");
    const imageName = (imgNameInput?.value || selectedRefImage?.name || "").trim();

    if (!imageName) {
      if (window.showCyberToast) window.showCyberToast("Select or type a reference image name", "error");
      return;
    }

    const btn = document.getElementById("runSketchBtn");
    btn.disabled = true;
    btn.innerHTML = `<span>ANIMATING...</span>`;
    if (window.showCyberToast) window.showCyberToast("Shadow AI contour animator engaged", "info");

    // Play pencil audio feedback
    const audio = new Audio("/static/image/pencil-sound.mp3");
    audio.volume = 0.4;
    audio.play().catch(() => {});

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `draw sketch ${imageName}` })
      });
      const data = await res.json().catch(() => ({}));
      if (window.showCyberToast) window.showCyberToast(data.response || "Contour sketch complete", "success");
    } catch (err) {
      if (window.showCyberToast) window.showCyberToast("Failed to reach sketch engine", "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>RUN CONTOUR SKETCH</span>`;
    }
  });

  // Initialise default tab
  switchTab("draw");
})();

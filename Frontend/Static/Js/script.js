/*************************************************
 * S.H.A.D.O.W. AI Dashboard - Master Script
 * Complete Navigation, Search AI, HUD Modals,
 * Preserved Backend Integration & Robust Error Safety
 *************************************************/

// Basic DOM Helper
const $ = (id) => document.getElementById(id);

function safeText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function safeWidth(id, percent) {
  const el = $(id);
  if (el) el.style.width = percent + "%";
}

/*************************************************
 * UI ELEMENT REFERENCES
 *************************************************/
const micBtn = $("voiceButton");
const micStatus = $("mic-status");
const cameraToggle = $("cameraToggle");
const cameraFeed = $("cameraFeed");
const toggleText = cameraToggle?.querySelector(".toggle-text");
const historyPanel = $("historyPanel");
const historyCloseBtn = $("historyCloseBtn");
const navbarSettingsBtn = $("navbarSettingsBtn");
const settingsMenu = $("settings-menu");
const inputBox = $("input-box");
const chatInput = $("chatInput");
const sendButton = $("sendButton");
const plusButton = $("plusButton");

// Navigation & Search Elements
const navSidebar = $("navSidebar");
const sidebarToggle = $("sidebarToggle");
const sidebarBackdrop = $("sidebarBackdrop");
const navbarSearchInput = $("navbarSearchInput");
const searchDropdown = $("searchDropdown");
const clearSearchBtn = $("clearSearchBtn");
const notifBtn = $("notifBtn");
const notifDropdown = $("notifDropdown");
const navbarProfileBtn = $("navbarProfileBtn");

// Intelligent Response UI Elements
const ringsContainer = document.querySelector(".rings-container");
const responseText = $("response-text");

/*************************************************
 * CONFIGURATION & STATE
 *************************************************/
const WAKE_WORD = "shadow";

let micState = "passive"; // passive | active
let manualMode = false;
let finalTranscript = "";
let silenceTimer = null;
let cameraStream = null;
let cameraOn = false;
let isRecognitionStarted = false;
let recognitionActive = false;
let restartCooldown = false;
let lastResultTime = 0;
let isSpeaking = false;

// Searchable Navigation Registry (Updated with exact menu items)
const SEARCH_ITEMS = [
  { id: "dashboard", name: "Dashboard", icon: "◉", category: "Navigation", target: "dashboard" },
  { id: "chatbot", name: "AI Chatbot", icon: "◉", category: "Core AI", target: "chatbot" },
  { id: "image", name: "Image", icon: "◉", category: "AI Studio", target: "image" },
  { id: "sketch", name: "Sketch", icon: "◉", category: "AI Studio", target: "sketch" },
  { id: "music", name: "Music", icon: "◉", category: "AI Studio", target: "music" },
  { id: "files", name: "Files", icon: "◉", category: "Vault", target: "files" },
  { id: "apikeys", name: "API Keys", icon: "▤", category: "System", target: "apikeys" },
  { id: "upgrade", name: "Upgrade", icon: "◆", category: "Firmware", target: "upgrade" },
  { id: "profile", name: "Profile", icon: "◎", category: "Identity", target: "profile" }
];

/*************************************************
 * SPEECH RECOGNITION SETUP (SAFE & CRASH-PROOF)
 *************************************************/
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
  try {
    recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      recognitionActive = true;
    };

    recognition.onaudiostart = () => {
      lastResultTime = Date.now();
    };

    recognition.onspeechstart = () => {
      lastResultTime = Date.now();
    };

    recognition.onend = () => {
      recognitionActive = false;
      if (isRecognitionStarted && !restartCooldown) {
        restartCooldown = true;
        setTimeout(() => {
          restartCooldown = false;
          if (isRecognitionStarted && !recognitionActive) {
            try {
              recognition.start();
            } catch (e) {
              if (e.name !== "InvalidStateError") {
                console.error("Error restarting mic:", e);
              }
            }
          }
        }, 300);
      }
    };

    recognition.onerror = (event) => {
      const errorCode = event.error;
      if (errorCode === "no-speech" || errorCode === "network" || errorCode === "aborted") {
        return;
      }
      console.warn("Mic error:", errorCode);
      if (errorCode === "not-allowed") {
        showStatus("Mic permission denied");
        showToast("Microphone access permission denied.", "error");
        isRecognitionStarted = false;
        updateMicUI(false);
      } else {
        showStatus(`Mic: ${errorCode}`);
      }
    };

    recognition.onresult = (event) => {
      if (!event.results.length) return;
      const lastResult = event.results[event.results.length - 1];
      if (!lastResult || !lastResult.length) return;

      const text = lastResult[0].transcript.toLowerCase().trim();
      if (!text) return;

      lastResultTime = Date.now();

      // Ignore mic input during AI speech playback
      if (isSpeaking) return;

      // Passive Mode: Wait for wake word
      if (micState === "passive" && !manualMode) {
        if (text.includes(WAKE_WORD) || text.startsWith("astra") || text.startsWith("shadow")) {
          micState = "active";
          finalTranscript = text.replace(WAKE_WORD, "").replace("astra", "").replace("shadow", "").trim();
          updateMicUI(true);
          showStatus("Listening...");
        }
        return;
      }

      // Active Mode: Collect speech command
      if (micState === "active") {
        updateMicUI(true);
        finalTranscript += " " + text;
        resetSilenceTimer();
      }
    };
  } catch (err) {
    console.error("Failed to construct SpeechRecognition:", err);
    recognition = null;
  }
} else {
  console.warn("Speech recognition not supported in this browser environment.");
}

function showStatus(statusText) {
  safeText("mic-status", statusText);
}

function startMic() {
  if (!recognition) {
    showStatus("Voice input unavailable");
    showToast("Speech Recognition not supported in this browser.", "info");
    return;
  }

  if (!isRecognitionStarted) {
    try {
      recognition.start();
      isRecognitionStarted = true;
      console.log("[SHADOW AI] Speech recognition started");
    } catch (e) {
      if (e.name !== "InvalidStateError") {
        console.error("Failed to start mic:", e);
      }
    }
  }
}

function resetSilenceTimer() {
  clearTimeout(silenceTimer);
  silenceTimer = setTimeout(submitVoiceCommand, 1600);
}

function submitVoiceCommand() {
  if (!finalTranscript.trim() || micState !== "active") {
    resetMic();
    return;
  }

  const clean = finalTranscript.replace(new RegExp(WAKE_WORD, "gi"), "").trim();
  if (!clean) {
    resetMic();
    return;
  }

  sendToBackend(clean, true);
  resetMic();
}

function resetMic() {
  micState = "passive";
  manualMode = false;
  finalTranscript = "";
  safeText("mic-status", "");
  updateMicUI(false);
}

/*************************************************
 * MIC UI STATE & AI RINGS ANIMATION FIX
 *************************************************/
function micActive() {
  const rings = document.querySelectorAll(".ring");
  rings.forEach((ring) => {
    ring.style.animationPlayState = "running";
  });
}

function micInactive() {
  const rings = document.querySelectorAll(".ring");
  rings.forEach((ring) => {
    ring.style.animationPlayState = "paused";
  });
}

function updateMicUI(isActive) {
  const container = $("container");
  const interactionZone = $("interaction-zone");
  const boxes = document.querySelectorAll(".box");

  if (isActive) {
    micBtn?.classList.add("active");
    container?.classList.add("mic-active");
    interactionZone?.classList.add("mic-active");
    boxes.forEach((box) => box.classList.add("mic-active"));

    // Activate sound visualization
    $("sound-gif-left")?.classList.add("visible");
    $("sound-gif-right")?.classList.add("visible");

    micActive();
  } else {
    micBtn?.classList.remove("active");
    container?.classList.remove("mic-active");
    interactionZone?.classList.remove("mic-active");
    boxes.forEach((box) => box.classList.remove("mic-active"));

    $("sound-gif-left")?.classList.remove("visible");
    $("sound-gif-right")?.classList.remove("visible");

    micActive(); // Rings continue ambient spin in passive mode
  }
}

micBtn?.addEventListener("click", () => {
  if (!recognition) {
    showStatus("Voice input unavailable");
    showToast("Microphone speech recognition is not supported in this browser.", "info");
    return;
  }

  if (!isRecognitionStarted) {
    startMic();
    manualMode = true;
    micState = "active";
    finalTranscript = "";
    updateMicUI(true);
    showStatus("Listening...");
    return;
  }

  if (micState === "active") {
    resetMic();
  } else {
    manualMode = true;
    micState = "active";
    finalTranscript = "";
    updateMicUI(true);
    showStatus("Listening...");
  }
});

/*************************************************
 * INTELLIGENT AI RESPONSE - CRASH-PROOF & REUSABLE
 * Fixed bug: Timers are cleaned up on every call,
 * inline opacity/styles are reset, and consecutive
 * commands always render text reliably.
 *************************************************/
let activeTypingTimeout = null;
let activeHideTimeout = null;

function showAIResponse(text) {
  if (!text) return;
  const resEl = $("response-text") || responseText;
  const ringsEl = document.querySelector(".rings-container") || ringsContainer;
  if (!resEl) return;

  // 1. Cancel any existing typing or hide timers
  if (activeTypingTimeout) {
    clearTimeout(activeTypingTimeout);
    activeTypingTimeout = null;
  }
  if (activeHideTimeout) {
    clearTimeout(activeHideTimeout);
    activeHideTimeout = null;
  }

  // 2. Cleanly reset element content and styles
  resEl.textContent = "";
  resEl.style.opacity = "1";
  resEl.style.transform = "translate(-50%, -50%) scale(1)";
  resEl.classList.remove("hidden");
  resEl.classList.add("response-active");

  // 3. Temporarily focus rings
  if (ringsEl) {
    ringsEl.style.transform = "translate(-50%, -50%) scale(0.45)";
    ringsEl.style.opacity = "0.35";
  }

  // 4. Clean character-by-character typewriter
  let i = 0;
  const fullText = String(text);

  function typeChar() {
    if (i < fullText.length) {
      resEl.textContent = fullText.substring(0, i + 1);
      i++;
      activeTypingTimeout = setTimeout(typeChar, 25);
    } else {
      activeTypingTimeout = null;
      // Auto fade-out after 6 seconds of inactivity
      activeHideTimeout = setTimeout(() => {
        resEl.classList.remove("response-active");
        resEl.style.opacity = "0";
        if (ringsEl) {
          ringsEl.style.transform = "translate(-50%, -50%) scale(1)";
          ringsEl.style.opacity = "1";
        }
      }, 6000);
    }
  }

  typeChar();
}

/*************************************************
 * BACKEND COMMUNICATION & CHAT
 * Text display & TTS operate independently
 *************************************************/
async function sendToBackend(text, fromMic = false) {
  if (!text || !text.trim()) return;

  showStatus("Processing...");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        from_mic: fromMic
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();
    showStatus("");

    const aiMsg = data.response || "Command executed successfully.";

    // 1. Render AI Response text immediately
    showAIResponse(aiMsg);

    // 2. Play TTS audio in parallel
    speak(aiMsg);

    if (data.exit) {
      setTimeout(() => window.close(), 2500);
    } else {
      if (historyPanel && !historyPanel.classList.contains("hidden")) {
        loadChatHistory();
      }
    }
  } catch (e) {
    console.error("Backend error:", e);
    showStatus("");
    // Standalone fallback response
    const fallbackMsg = `S.H.A.D.O.W. Core received: "${text}"`;
    showAIResponse(fallbackMsg);
    speak(fallbackMsg);
  }
}

let activeAudioObj = null;

function stopCurrentAudio() {
  if (activeAudioObj) {
    try {
      activeAudioObj.pause();
      activeAudioObj.currentTime = 0;
    } catch (err) {
      console.warn("TTS cleanup warning:", err);
    }
    activeAudioObj = null;
  }
}

async function speak(text) {
  if (!text || !text.trim()) return;

  stopCurrentAudio();
  console.log("[TTS] frontend playback started for response text length:", text.length);

  try {
    $("sound-gif-left")?.classList.add("visible");
    $("sound-gif-right")?.classList.add("visible");

    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok || !data.audio_url) {
      console.warn("[TTS] backend TTS failed:", data.message || "unknown error");
      return;
    }

    const audioUrl = data.audio_url.startsWith("http") ? data.audio_url : `${window.location.origin}${data.audio_url}`;
    console.log("[TTS] audio URL returned:", audioUrl);

    const audio = new Audio(audioUrl);
    activeAudioObj = audio;
    audio.preload = "auto";
    audio.volume = 1;

    audio.onplay = () => {
      console.log("[TTS] frontend audio playback started");
    };

    audio.onended = () => {
      console.log("[TTS] frontend audio playback completed");
      if (activeAudioObj === audio) {
        activeAudioObj = null;
      }
      $("sound-gif-left")?.classList.remove("visible");
      $("sound-gif-right")?.classList.remove("visible");
    };

    audio.onerror = (event) => {
      console.error("[TTS] frontend audio playback error:", event);
      if (activeAudioObj === audio) {
        activeAudioObj = null;
      }
      $("sound-gif-left")?.classList.remove("visible");
      $("sound-gif-right")?.classList.remove("visible");
    };

    try {
      await audio.play();
    } catch (playErr) {
      console.warn("[TTS] autoplay rejected:", playErr);
      $("sound-gif-left")?.classList.remove("visible");
      $("sound-gif-right")?.classList.remove("visible");
    }
  } catch (e) {
    console.warn("[TTS] backend TTS request failed:", e);
  } finally {
    isSpeaking = false;
  }
}

// Chat input event listeners
chatInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const val = chatInput.value.trim();
    if (!val) return;
    sendToBackend(val, false);
    chatInput.value = "";
  }
});

sendButton?.addEventListener("click", () => {
  if (!chatInput) return;
  const val = chatInput.value.trim();
  if (!val) return;
  sendToBackend(val, false);
  chatInput.value = "";
});

plusButton?.addEventListener("click", () => {
  showToast("Context attachment module ready.", "info");
});

/*************************************************
 * TOP NAVBAR SEARCH AI FUNCTIONALITY
 *************************************************/
function initSearchAI() {
  if (!navbarSearchInput || !searchDropdown) return;

  navbarSearchInput.addEventListener("input", (e) => {
    const query = e.target.value.trim().toLowerCase();
    if (!query) {
      searchDropdown.classList.add("hidden");
      searchDropdown.innerHTML = "";
      clearSearchBtn?.classList.add("hidden");
      return;
    }

    clearSearchBtn?.classList.remove("hidden");

    // Filter registry
    const matches = SEARCH_ITEMS.filter(
      (item) => item.name.toLowerCase().includes(query) || item.id.toLowerCase().includes(query) || item.category.toLowerCase().includes(query)
    );

    renderSearchResults(matches);
  });

  navbarSearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeSearch();
      return;
    }

    const items = searchDropdown.querySelectorAll(".search-result-item");
    if (!items.length) return;

    let highlightedIndex = Array.from(items).findIndex((item) => item.classList.contains("highlighted"));

    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (highlightedIndex < items.length - 1) {
        if (highlightedIndex >= 0) items[highlightedIndex].classList.remove("highlighted");
        items[highlightedIndex + 1].classList.add("highlighted");
        items[highlightedIndex + 1].scrollIntoView({ block: "nearest" });
      } else if (highlightedIndex === -1) {
        items[0].classList.add("highlighted");
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (highlightedIndex > 0) {
        items[highlightedIndex].classList.remove("highlighted");
        items[highlightedIndex - 1].classList.add("highlighted");
        items[highlightedIndex - 1].scrollIntoView({ block: "nearest" });
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightedIndex >= 0) {
        items[highlightedIndex].click();
      } else if (items.length > 0) {
        items[0].click();
      }
    }
  });

  clearSearchBtn?.addEventListener("click", () => {
    navbarSearchInput.value = "";
    closeSearch();
    navbarSearchInput.focus();
  });
}

function renderSearchResults(matches) {
  if (!searchDropdown) return;
  searchDropdown.innerHTML = "";

  if (matches.length === 0) {
    searchDropdown.innerHTML = '<div class="search-no-results">No matching modules found</div>';
    searchDropdown.classList.remove("hidden");
    return;
  }

  matches.forEach((item, index) => {
    const el = document.createElement("div");
    el.className = `search-result-item ${index === 0 ? "highlighted" : ""}`;
    el.setAttribute("role", "option");
    el.innerHTML = `
      <span class="search-result-icon">${item.icon}</span>
      <span class="search-result-name">${item.name}</span>
      <span class="search-result-category">${item.category}</span>
    `;

    el.addEventListener("click", () => {
      handleNavigation(item.target);
      closeSearch();
      navbarSearchInput.value = "";
    });

    searchDropdown.appendChild(el);
  });

  searchDropdown.classList.remove("hidden");
}

function closeSearch() {
  if (searchDropdown) searchDropdown.classList.add("hidden");
  if (clearSearchBtn) clearSearchBtn.classList.add("hidden");
}

/*************************************************
 * SIDEBAR NAVIGATION & ROUTING HANDLER
 *************************************************/
function initSidebarNav() {
  // Mobile / Tablet Drawer Toggle
  sidebarToggle?.addEventListener("click", () => {
    const isOpen = navSidebar?.classList.contains("open");
    if (isOpen) {
      closeSidebarDrawer();
    } else {
      openSidebarDrawer();
    }
  });

  sidebarBackdrop?.addEventListener("click", closeSidebarDrawer);

  // Sidebar Links
  document.querySelectorAll(".sidebar-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const target = link.getAttribute("data-nav");
      if (target) {
        handleNavigation(target);
      }
      closeSidebarDrawer();
    });
  });
}

function openSidebarDrawer() {
  navSidebar?.classList.add("open");
  sidebarBackdrop?.classList.add("show");
}

function closeSidebarDrawer() {
  navSidebar?.classList.remove("open");
  sidebarBackdrop?.classList.remove("show");
}

function setActiveNavLink(targetId) {
  document.querySelectorAll(".sidebar-link").forEach((link) => {
    if (link.getAttribute("data-nav") === targetId) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });
}

function handleNavigation(target) {
  setActiveNavLink(target);

  switch (target) {
    case "dashboard":
      closeAllModals();
      window.scrollTo({ top: 0, behavior: "smooth" });
      showToast("Dashboard active", "info");
      break;

    case "chatbot":
      // If Flask chatbot route exists, or focus chat
      if (window.location.pathname !== "/chatbot") {
        if (inputBox) inputBox.style.display = "flex";
        chatInput?.focus();
        showToast("AI Chat interface active", "info");
      }
      break;

    case "image":
      openModal("imageModal");
      break;

    case "sketch":
      openModal("sketchModal");
      initCanvas();
      break;

    case "music":
      openModal("musicModal");
      break;

    case "files":
      openModal("filesModal");
      break;

    case "apikeys":
      openLogs();
      break;

    case "upgrade":
      openModal("upgradeModal");
      break;

    case "profile":
      openModal("profileModal");
      break;

    default:
      console.log("Nav target:", target);
  }
}

/*************************************************
 * MODAL MANAGEMENT
 *************************************************/
function openModal(modalId) {
  const modal = $(modalId);
  if (modal) {
    modal.classList.remove("hidden");
  }
}

function closeModal(modalId) {
  const modal = $(modalId);
  if (modal) {
    modal.classList.add("hidden");
  }
}

function closeAllModals() {
  document.querySelectorAll(".modal").forEach((m) => m.classList.add("hidden"));
  if (historyPanel) historyPanel.classList.add("hidden");
  if (notifDropdown) notifDropdown.classList.add("hidden");
  if (settingsMenu) {
    settingsMenu.style.display = "none";
    settingsMenu.classList.remove("show");
  }
}

// Modal close button event delegation
document.addEventListener("click", (e) => {
  const closeBtn = e.target.closest("[data-close-modal]");
  if (closeBtn) {
    const modalId = closeBtn.getAttribute("data-close-modal");
    if (modalId) closeModal(modalId);
  }
});

/*************************************************
 * TOP NAVBAR ACTIONS (NOTIFICATIONS, PROFILE, SETTINGS)
 *************************************************/
function initTopNavbarActions() {
  // Notifications Dropdown
  notifBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    notifDropdown?.classList.toggle("hidden");
    const badge = $("notifBadge");
    if (badge) badge.style.display = "none";
  });

  $("clearNotifsBtn")?.addEventListener("click", () => {
    const list = $("notifList");
    if (list) {
      list.innerHTML = '<div style="padding: 20px; text-align: center; color: rgba(0,234,255,0.6); font-size:0.8rem;">No active alerts</div>';
    }
  });

  // Settings Button in Navbar
  navbarSettingsBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    if (!settingsMenu) return;
    const isShowing = settingsMenu.classList.contains("show") || settingsMenu.style.display === "flex";
    if (isShowing) {
      settingsMenu.style.display = "none";
      settingsMenu.classList.remove("show");
    } else {
      settingsMenu.style.display = "flex";
      settingsMenu.classList.add("show");
    }
  });

  // Settings Menu Navigation
  document.querySelectorAll("#settings-menu button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const page = btn.getAttribute("data-page");
      if (page === "input-box") {
        if (inputBox) {
          const isOpen = inputBox.style.display !== "none";
          inputBox.style.display = isOpen ? "none" : "flex";
          localStorage.setItem("isSearchBoxOpen", !isOpen);
          if (!isOpen) inputBox.scrollIntoView({ behavior: "smooth", block: "end" });
        }
      } else if (page === "history") {
        openHistory();
      } else if (page === "logs") {
        openLogs();
      } else if (page === "chatbot") {
        window.location.href = "/chatbot";
      }
      if (settingsMenu) {
        settingsMenu.style.display = "none";
        settingsMenu.classList.remove("show");
      }
    });
  });

  // Close dropdowns on outside click
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#notifBtn") && !e.target.closest("#notifDropdown")) {
      notifDropdown?.classList.add("hidden");
    }
    if (!e.target.closest("#navbarSettingsBtn") && !e.target.closest("#settings-menu")) {
      if (settingsMenu) {
        settingsMenu.style.display = "none";
        settingsMenu.classList.remove("show");
      }
    }
    if (!e.target.closest(".search-ai-container")) {
      closeSearch();
    }
  });

  // Profile Button
  navbarProfileBtn?.addEventListener("click", () => {
    openModal("profileModal");
  });
}

/*************************************************
 * SKETCH CANVAS MODULE
 *************************************************/
let isDrawing = false;
let canvasCtx = null;

function initCanvas() {
  const canvas = $("sketchCanvas");
  if (!canvas) return;
  canvasCtx = canvas.getContext("2d");

  // Initial canvas styling
  canvasCtx.strokeStyle = "#00eaff";
  canvasCtx.lineWidth = 2;
  canvasCtx.lineCap = "round";

  const startDraw = (e) => {
    isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    canvasCtx.beginPath();
    canvasCtx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    canvasCtx.lineTo(x, y);
    canvasCtx.stroke();
  };

  const stopDraw = () => {
    isDrawing = false;
  };

  canvas.addEventListener("mousedown", startDraw);
  canvas.addEventListener("mousemove", draw);
  canvas.addEventListener("mouseup", stopDraw);
  canvas.addEventListener("mouseleave", stopDraw);

  canvas.addEventListener("touchstart", startDraw, { passive: true });
  canvas.addEventListener("touchmove", draw, { passive: true });
  canvas.addEventListener("touchend", stopDraw);

  $("clearCanvasBtn")?.addEventListener("click", () => {
    canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
  });
}

/*************************************************
 * IMAGE SYNTHESIS GENERATOR
 *************************************************/
$("generateImageBtn")?.addEventListener("click", () => {
  const input = $("imagePromptInput");
  const box = $("imagePreviewBox");
  if (!input || !box) return;

  const prompt = input.value.trim();
  if (!prompt) {
    showToast("Please enter a prompt first", "info");
    return;
  }

  box.innerHTML = '<div style="color:var(--color-primary); letter-spacing:2px;">SYNTHESIZING NEURAL VISUAL...</div>';
  setTimeout(() => {
    box.innerHTML = `<div style="text-align:center; color:#39ff14;"><strong>Render Complete:</strong><br><small style="color:var(--color-text-secondary);">${prompt}</small><br><br><span style="color:var(--color-primary); font-size:2rem;">❖</span></div>`;
    showToast("Image generation complete", "success");
  }, 1800);
});

/*************************************************
 * OTA UPGRADE CHECK
 *************************************************/
$("checkUpdateBtn")?.addEventListener("click", () => {
  const btn = $("checkUpdateBtn");
  if (btn) {
    btn.textContent = "Scanning OTA Server...";
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = "System Up to Date (v2.0.4)";
      btn.disabled = false;
      showToast("Kernel firmware is optimal.", "success");
    }, 1500);
  }
});

/*************************************************
 * TOAST NOTIFICATION HELPER
 *************************************************/
function showToast(message, type = "info") {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/*************************************************
 * CAMERA FEED MODULE
 *************************************************/
cameraToggle?.addEventListener("click", toggleCamera);

async function toggleCamera() {
  if (cameraOn) {
    stopCamera();
  } else {
    await startCamera();
  }
}

async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    });

    if (cameraFeed) {
      cameraFeed.srcObject = cameraStream;
      cameraFeed.style.display = "block";
    }

    cameraOn = true;
    cameraToggle?.classList.add("on");
    if (toggleText) toggleText.innerText = "ON";
    showToast("Visual input activated", "success");
  } catch (err) {
    console.error("Camera access error:", err);
    showToast("Camera access unavailable.", "error");
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }

  if (cameraFeed) {
    cameraFeed.srcObject = null;
    cameraFeed.style.display = "none";
  }

  cameraOn = false;
  cameraToggle?.classList.remove("on");
  if (toggleText) toggleText.innerText = "OFF";
  showToast("Visual input deactivated", "info");
}

/*************************************************
 * SYSTEM STATUS, CPU & MEMORY TELEMETRY
 *************************************************/
async function updateTelemetry() {
  try {
    const res = await fetch("/api/system-stats");
    if (res.ok) {
      const data = await res.json();
      if (data.cpu !== undefined) {
        safeText("cpu", data.cpu);
        safeWidth("cpu-bar", data.cpu);
      }
      if (data.memory_used !== undefined) {
        safeText("memory-used", data.memory_used);
        safeText("memory-total", data.memory_total || "16");
        const pct = Math.round((data.memory_used / (data.memory_total || 16)) * 100);
        safeWidth("memory-bar", pct);
      }
      if (data.storage_used !== undefined) {
        safeText("storage-used", data.storage_used);
        safeText("storage-total", data.storage_total || "512");
        const pct = Math.round((data.storage_used / (data.storage_total || 512)) * 100);
        safeWidth("storage-bar", pct);
      }
      if (data.power !== undefined) {
        safeText("power", data.power);
        const bText = $("battery-level-text");
        if (bText) bText.textContent = `ON BATTERY ${data.power}%`;
      }
    }
  } catch (err) {
    // Graceful fallback for standalone preview
  }
}

/*************************************************
 * ENVIRONMENT / WEATHER TELEMETRY
 *************************************************/
async function updateWeather() {
  try {
    const res = await fetch("/api/weather");
    if (res.ok) {
      const data = await res.json();
      safeText("city", data.city || "Pune");
      safeText("temperature", data.temperature || "22°C");
      safeText("weather-status", data.status || "Clear");
      safeText("weather-details", data.details || "The skies will be mostly clear. Low 18°C.");
      safeText("feels-like", data.feels || "24°C");
      safeText("wind", data.wind || "1 km/h");
      safeText("humidity", data.humidity || "95%");
    }
  } catch (err) {
    // Graceful fallback
  }
}

/*************************************************
 * TIME & DATE CLOCK (LIVE TICK)
 *************************************************/
function updateTimeClock() {
  const now = new Date();
  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  safeText("month", months[now.getMonth()]);
  safeText("year", now.getFullYear());
  safeText("day", now.getDate());
  safeText("day-name", days[now.getDay()]);

  let hours = now.getHours();
  const minutes = String(now.getMinutes()).padStart(2, "0");
  const seconds = String(now.getSeconds()).padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12 || 12;
  const strHours = String(hours).padStart(2, "0");

  safeText("time", `${strHours}:${minutes}:${seconds} ${ampm}`);
}

/*************************************************
 * HISTORY & LOGS PANEL
 *************************************************/
historyCloseBtn?.addEventListener("click", () => {
  historyPanel?.classList.add("hidden");
});

function openHistory() {
  if (historyPanel) {
    historyPanel.classList.remove("hidden");
    loadChatHistory();
  }
}

async function loadChatHistory(date = null) {
  const body = historyPanel?.querySelector(".history-body");
  if (!body) return;

  try {
    const url = date ? `/api/history?date=${date}` : "/api/history";
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      renderHistory(data);
    } else {
      renderHistorySample();
    }
  } catch {
    renderHistorySample();
  }
}

function renderHistory(items) {
  const body = historyPanel?.querySelector(".history-body");
  if (!body) return;

  if (!items || !items.length) {
    body.innerHTML = '<div style="padding:20px; text-align:center; color:var(--color-text-dim);">No conversation logs found</div>';
    return;
  }

  body.innerHTML = items
    .map(
      (it) => `
    <div class="history-row ${it.role === "user" ? "user-msg" : "ai-msg"}">
      <div>
        <strong class="history-text ${it.role}">${it.role === "user" ? "USER" : "SHADOW AI"}:</strong>
        <span>${it.message}</span>
      </div>
      <button class="copy-btn" onclick="navigator.clipboard.writeText('${it.message.replace(/'/g, "\\'")}')">Copy</button>
    </div>
  `
    )
    .join("");
}

function renderHistorySample() {
  renderHistory([
    { role: "user", message: "Initialize diagnostic scan" },
    { role: "ai", message: "All neural cores and sensory arrays running at 100% nominal capacity." },
    { role: "user", message: "Report weather telemetry" },
    { role: "ai", message: "Current conditions in Pune: 22°C, mostly clear, humidity 95%." }
  ]);
}

// LOGS / API KEYS PANEL
function openLogs() {
  const logsPanel = $("logsPanel");
  const logsBackdrop = $("logsBackdrop");
  if (logsPanel) {
    logsPanel.classList.remove("hidden");
    logsPanel.setAttribute("aria-hidden", "false");
    if (logsBackdrop) logsBackdrop.classList.add("show");
    loadEnvVariables();
  }
}

function closeLogs() {
  const logsPanel = $("logsPanel");
  const logsBackdrop = $("logsBackdrop");
  if (logsPanel) {
    logsPanel.classList.add("hidden");
    logsPanel.setAttribute("aria-hidden", "true");
    if (logsBackdrop) logsBackdrop.classList.remove("show");
  }
}

$("logsCloseBtn")?.addEventListener("click", closeLogs);
$("logsBackdrop")?.addEventListener("click", closeLogs);

function loadEnvVariables() {
  const body = $("logsPanel")?.querySelector(".logs-body");
  if (!body) return;

  const envs = [
    { key: "COHERE_API_KEY", value: "sk-co-live-••••••••••••" },
    { key: "WEATHER_API_KEY", value: "owm-live-••••••••••••" },
    { key: "NEWS_API_KEY", value: "news-api-••••••••••••" },
    { key: "SECURITY_LEVEL", value: "LEVEL_5_MILSPEC" },
    { key: "NETWORK_PORT", value: "5000" }
  ];

  body.innerHTML = envs
    .map(
      (env) => `
    <div class="env-row">
      <span class="env-label">${env.key}</span>
      <span class="env-value" id="val-${env.key}">${env.value}</span>
      <button class="env-edit-btn" onclick="editEnvKey('${env.key}')">Edit</button>
    </div>
  `
    )
    .join("");
}

window.editEnvKey = function (key) {
  const valEl = $(`val-${key}`);
  if (!valEl) return;
  const currentVal = valEl.textContent;
  valEl.innerHTML = `<input type="text" class="env-input" id="input-${key}" value="${currentVal}">`;
  const btn = valEl.nextElementSibling;
  if (btn) {
    btn.textContent = "Save";
    btn.classList.add("update-btn");
    btn.onclick = () => saveEnvKey(key);
  }
};

window.saveEnvKey = function (key) {
  const input = $(`input-${key}`);
  if (!input) return;
  const newVal = input.value.trim();
  const valEl = $(`val-${key}`);
  if (valEl) valEl.textContent = newVal || "••••••••";
  const btn = valEl?.nextElementSibling;
  if (btn) {
    btn.textContent = "Edit";
    btn.classList.remove("update-btn");
    btn.onclick = () => window.editEnvKey(key);
  }
  showToast(`Updated ${key}`, "success");
};

/*************************************************
 * INITIALIZATION ON DOM READY
 *************************************************/
document.addEventListener("DOMContentLoaded", () => {
  initTopNavbarActions();
  initSidebarNav();
  initSearchAI();

  // Clock ticks every second
  updateTimeClock();
  setInterval(updateTimeClock, 1000);

  // Status updates
  updateTelemetry();
  setInterval(updateTelemetry, 5000);

  updateWeather();
  setInterval(updateWeather, 60000);

  // Restore input box state preference
  const isSearchOpen = localStorage.getItem("isSearchBoxOpen");
  if (isSearchOpen === "false" && inputBox) {
    inputBox.style.display = "none";
  }

  console.log("S.H.A.D.O.W. AI Master System Initialized.");
});

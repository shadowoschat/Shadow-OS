/**
 * SHADOW OS — AI Chatbot Workstation Controller
 * Live message stream with real timestamps, Semicircle HUD animations,
 * Scrollable Chat Sessions sidebar, Web Speech API & TTS
 */

(function () {
  "use strict";

  let isListening = false;
  let recognition = null;
  let currentActiveSessionIdx = -1;

  document.addEventListener("DOMContentLoaded", () => {
    initChatInterface();
    initHistorySidebar();
    initSpeechRec();
    initPromptChips();

    const greetingTime = document.getElementById("initialGreetingTime");
    if (greetingTime) {
      greetingTime.textContent = formatCurrentTime();
    }
  });

  /* --------------------------------------------------------------------------
     1. SEMICIRCLE HUD STATE CONTROLLER
     -------------------------------------------------------------------------- */
  function setSemicircleState(state, customLabel) {
    const hud = document.getElementById("semicircleHud");
    const labelEl = document.getElementById("semicircleStateLabel");
    if (!hud) return;

    hud.setAttribute("data-state", state);

    let defaultLabel = "SHADOWCOGNITIVE MATRIX // IDLE";
    if (state === "sending" || state === "listening") {
      defaultLabel = "RECEPTOR ENGAGED // LISTENING DIRECTIVE";
    } else if (state === "processing") {
      defaultLabel = "FIRST-LAYER DMM // PROCESSING TASK...";
    } else if (state === "response") {
      defaultLabel = "SYNTHESIS DISPATCHED // NOMINAL";
    }

    if (labelEl) {
      labelEl.textContent = customLabel || defaultLabel;
    }
  }

  function formatCurrentTime(dateObj = new Date()) {
    try {
      return dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    } catch {
      return "";
    }
  }

  /* --------------------------------------------------------------------------
     2. CHAT INTERFACE & MESSAGING
     -------------------------------------------------------------------------- */
  function initChatInterface() {
    const input = document.getElementById("chatMsgInput");
    const sendBtn = document.getElementById("chatSendBtn");
    const clearBtn = document.getElementById("clearChatBtn");
    const messagesContainer = document.getElementById("chatMessages");

    function sendMessage() {
      const text = (input?.value || "").trim();
      if (!text) return;

      appendMessage("user", text);
      if (input) input.value = "";

      setSemicircleState("sending", "TRANSMITTING NEURAL DIRECTIVE...");
      fetchAIResponse(text);
    }

    sendBtn?.addEventListener("click", sendMessage);
    input?.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    clearBtn?.addEventListener("click", () => {
      if (messagesContainer) {
        const timeNow = formatCurrentTime();
        messagesContainer.innerHTML = `
          <div class="message-row ai-msg">
            <div class="msg-avatar">
              <img src="/static/image/robot.svg" alt="SHADOWAI" />
            </div>
            <div class="msg-bubble-wrap">
              <div class="msg-bubble">
                Chat buffer cleared. SHADOW Neural Core is standing by for instructions.
              </div>
              <span class="msg-timestamp">${timeNow}</span>
            </div>
          </div>
        `;
      }
      setSemicircleState("idle");
    });
  }

  async function fetchAIResponse(userText) {
    const messagesContainer = document.getElementById("chatMessages");
    
    // Switch semicircle HUD to AI PROCESSING state
    setTimeout(() => {
      setSemicircleState("processing", "AI PROCESSING // DMM REASONING...");
    }, 300);

    // Add temporary typing indicator bubble
    const typingId = "typing_" + Date.now();
    const typingRow = document.createElement("div");
    typingRow.className = "message-row ai-msg";
    typingRow.id = typingId;
    typingRow.innerHTML = `
      <div class="msg-avatar">
        <img src="/static/image/robot.svg" alt="SHADOWAI" />
      </div>
      <div class="msg-bubble-wrap">
        <div class="msg-bubble" style="color: var(--cyan);">
          <em>Neural core synthesizing response...</em>
        </div>
      </div>
    `;
    messagesContainer?.appendChild(typingRow);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText })
      });

      const data = await res.json().catch(() => ({}));
      const reply = data.response || "Task executed.";

      // Remove typing indicator
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();

      // Trigger AI RESPONSE animation state
      setSemicircleState("response", "AI RESPONSE DISPATCHED");

      appendMessage("ai", reply);
      loadHistoryList(); // Refresh sidebar chat sessions

      // Return to IDLE after response animation
      setTimeout(() => {
        setSemicircleState("idle");
      }, 1600);

    } catch (err) {
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();
      appendMessage("ai", "Network error communicating with Shadow AI neural backend.");
      setSemicircleState("idle");
    }
  }

  function appendMessage(sender, text, timestampStr = null) {
    const container = document.getElementById("chatMessages");
    if (!container) return;

    const row = document.createElement("div");
    row.className = `message-row ${sender === "user" ? "user-msg" : "ai-msg"}`;

    const avatarSrc = sender === "user" ? "/static/image/logo.svg" : "/static/image/robot.svg";
    const senderName = sender === "user" ? "Operator" : "SHADOWAI";
    const timeDisplay = timestampStr || formatCurrentTime();

    row.innerHTML = `
      <div class="msg-avatar">
        <img src="${avatarSrc}" alt="${senderName}" />
      </div>
      <div class="msg-bubble-wrap">
        <div class="msg-bubble">
          <div>${escapeHtml(text)}</div>
          <div style="display: flex; gap: 8px; margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(0,234,255,0.1);">
            <button class="btn-copy" style="background: transparent; border: none; color: var(--cyan); font-size: 0.68rem; cursor: pointer; display: flex; align-items: center; gap: 4px; font-family: var(--font-mono);">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              COPY
            </button>
            ${sender === "ai" ? `
            <button class="btn-speak" style="background: transparent; border: none; color: var(--green); font-size: 0.68rem; cursor: pointer; display: flex; align-items: center; gap: 4px; font-family: var(--font-mono);">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
              SPEAK
            </button>` : ""}
          </div>
        </div>
        <span class="msg-timestamp">${timeDisplay}</span>
      </div>
    `;

    container.appendChild(row);
    container.scrollTop = container.scrollHeight;

    // Attach copy & speak events
    const copyBtn = row.querySelector(".btn-copy");
    copyBtn?.addEventListener("click", () => {
      navigator.clipboard.writeText(text);
      if (window.showCyberToast) window.showCyberToast("Message copied to clipboard", "success");
    });

    const speakBtn = row.querySelector(".btn-speak");
    speakBtn?.addEventListener("click", () => {
      speakMessage(text);
    });
  }

  let activeChatbotAudio = null;

  function stopChatbotAudio() {
    if (activeChatbotAudio) {
      try {
        activeChatbotAudio.pause();
        activeChatbotAudio.currentTime = 0;
      } catch (_) {}
      activeChatbotAudio = null;
    }
  }

  async function speakText(text) {
    if (!text || !text.trim()) return;
    stopChatbotAudio();
    console.log("[TTS] chatbot playback requested");

    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok || !data.audio_url) {
        console.warn("[TTS] chatbot backend failed:", data.message || "unknown error");
        return;
      }

      const audioUrl = data.audio_url.startsWith("http") ? data.audio_url : `${window.location.origin}${data.audio_url}`;
      console.log("[TTS] chatbot audio URL:", audioUrl);

      const audio = new Audio(audioUrl);
      activeChatbotAudio = audio;
      audio.volume = 1;

      audio.onplay = () => console.log("[TTS] chatbot audio started");
      audio.onended = () => {
        console.log("[TTS] chatbot audio completed");
        if (activeChatbotAudio === audio) activeChatbotAudio = null;
      };
      audio.onerror = (event) => {
        console.error("[TTS] chatbot audio error:", event);
        if (activeChatbotAudio === audio) activeChatbotAudio = null;
      };

      try {
        await audio.play();
      } catch (playErr) {
        console.warn("[TTS] chatbot autoplay rejected:", playErr);
      }
    } catch (e) {
      console.warn("[TTS] chatbot backend request failed:", e);
    }
  }

  /* --------------------------------------------------------------------------
     3. CHAT SESSIONS & HISTORY SIDEBAR
     -------------------------------------------------------------------------- */
  function initHistorySidebar() {
    const dateInput = document.getElementById("historyDateFilter");
    dateInput?.addEventListener("change", () => {
      loadHistoryList(dateInput.value);
    });

    loadHistoryList();
  }

  async function loadHistoryList(filterDate = null) {
    const listEl = document.getElementById("chatHistoryList");
    if (!listEl) return;

    try {
      let url = "/api/history";
      if (filterDate) url += `?date=${filterDate}`;

      const res = await fetch(url);
      const chats = await res.json().catch(() => []);

      if (chats.length === 0) {
        listEl.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 0.72rem; font-family: var(--font-mono);">NO RECENT SESSIONS FOUND</div>`;
        return;
      }

      listEl.innerHTML = "";
      chats.slice(0, 30).forEach((item, idx) => {
        const div = document.createElement("div");
        div.className = `history-item ${idx === currentActiveSessionIdx ? "active" : ""}`;

        // Format real timestamp or date
        let timeStr = "";
        if (item.timestamp) {
          try {
            timeStr = formatCurrentTime(new Date(item.timestamp * 1000));
          } catch {
            timeStr = item.date || "";
          }
        } else {
          timeStr = item.date || "";
        }

        const title = item.user_msg || "Conversation";
        const preview = item.response || "";

        div.innerHTML = `
          <div class="history-item-top">
            <span class="history-item-prompt">${escapeHtml(title)}</span>
            <span class="history-item-time">${timeStr}</span>
          </div>
          <div class="history-item-preview">${escapeHtml(preview)}</div>
        `;

        div.addEventListener("click", () => {
          // Mark active session state
          currentActiveSessionIdx = idx;
          document.querySelectorAll(".history-item").forEach(el => el.classList.remove("active"));
          div.classList.add("active");

          // Load into conversation view with real time
          appendMessage("user", item.user_msg, timeStr);
          appendMessage("ai", item.response, timeStr);
        });

        listEl.appendChild(div);
      });
    } catch (err) {
      console.warn("History load failed:", err);
      listEl.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--pink); font-size: 0.72rem; font-family: var(--font-mono);">SESSION LOG UNAVAILABLE</div>`;
    }
  }

  /* --------------------------------------------------------------------------
     4. SPEECH RECOGNITION (VOICE INPUT)
     -------------------------------------------------------------------------- */
  function initSpeechRec() {
    const micBtn = document.getElementById("chatMicBtn");
    const input = document.getElementById("chatMsgInput");

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      if (micBtn) micBtn.style.display = "none";
      return;
    }

    recognition = new SpeechRec();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      micBtn?.classList.add("listening");
      setSemicircleState("listening", "VOICE RECEPTOR ACTIVE // LISTENING...");
    };

    recognition.onend = () => {
      isListening = false;
      micBtn?.classList.remove("listening");
      setSemicircleState("idle");
    };

    recognition.onerror = () => {
      isListening = false;
      micBtn?.classList.remove("listening");
      setSemicircleState("idle");
    };

    recognition.onresult = (e) => {
      if (e.results.length > 0) {
        const transcript = e.results[0][0].transcript.trim();
        if (transcript) {
          if (input) input.value = transcript;
          appendMessage("user", transcript);
          if (input) input.value = "";
          fetchAIResponse(transcript);
        }
      }
    };

    micBtn?.addEventListener("click", () => {
      if (!isListening) {
        try {
          recognition.start();
        } catch {}
      } else {
        recognition.stop();
      }
    });
  }

  /* --------------------------------------------------------------------------
     5. QUICK PROMPT CHIPS
     -------------------------------------------------------------------------- */
  function initPromptChips() {
    const chips = document.querySelectorAll(".prompt-chip");
    const input = document.getElementById("chatMsgInput");

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const prompt = chip.getAttribute("data-prompt") || chip.textContent;
        if (input) {
          input.value = prompt;
          input.focus();
        }
      });
    });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
})();

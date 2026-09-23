/**
 * SHADOW OS — Dashboard Controller
 * Live Telemetry (CPU, RAM, Disk, Battery), Weather, Network, Camera Vision, Web Speech API & Chat Integration
 */

(function () {
  "use strict";

  let cameraStream = null;
  let isCameraOn = false;
  let isListening = false;
  let recognition = null;
  const WAKE_WORD = "Astra";

  document.addEventListener("DOMContentLoaded", () => {
    initSystemTelemetry();
    initWeatherTelemetry();
    initNetworkTelemetry();
    initCameraControls();
    initSpeechRecognition();
    initChatPrompt();
  });

  /* --------------------------------------------------------------------------
     1. SYSTEM TELEMETRY (CPU, Memory, Storage, Battery)
     -------------------------------------------------------------------------- */
  function initSystemTelemetry() {
    async function updateSystem() {
      try {
        const res = await fetch("/api/system-stats");
        if (!res.ok) return;
        const data = await res.json();

        // CPU
        const cpuVal = Math.round(data.cpu ?? 0);
        safeText("cpuVal", cpuVal + "%");
        safeWidth("cpuBar", cpuVal);

        // Memory
        const memUsed = (data.memory?.used ?? 0).toFixed(1);
        const memTotal = Math.round(data.memory?.total ?? 0);
        const memPct = Math.round(data.memory?.percent ?? 0);
        safeText("memVal", `${memUsed} / ${memTotal} GB (${memPct}%)`);
        safeWidth("memBar", memPct);

        // Storage
        const diskUsed = Math.round(data.storage?.used ?? 0);
        const diskTotal = Math.round(data.storage?.total ?? 0);
        const diskPct = Math.round(data.storage?.percent ?? 0);
        safeText("storageVal", `${diskUsed} / ${diskTotal} GB (${diskPct}%)`);
        safeWidth("storageBar", diskPct);

        // Battery / Power
        const battPct = Math.round(data.battery?.percent ?? 100);
        const charging = data.battery?.charging ?? false;
        const battText = document.getElementById("batteryText");
        const battStatus = document.getElementById("batteryStatus");
        const battBox = document.getElementById("batteryBadge");

        if (battText) {
          battText.textContent = `POWER: ${battPct}%`;
        }
        if (battStatus) {
          battStatus.textContent = charging ? "⚡ CHARGING" : (battPct > 90 ? "OPTIMAL" : "DISCHARGING");
        }

        if (battBox) {
          if (battPct < 30) {
            battBox.style.borderColor = "var(--pink)";
            if (battText) battText.style.color = "var(--pink)";
          } else if (battPct < 70) {
            battBox.style.borderColor = "var(--amber)";
            if (battText) battText.style.color = "var(--amber)";
          } else {
            battBox.style.borderColor = "rgba(0, 255, 157, 0.4)";
            if (battText) battText.style.color = "var(--green)";
          }
        }
      } catch (err) {
        console.warn("System telemetry fetch failed:", err);
      }
    }

    updateSystem();
    setInterval(updateSystem, 2500);
  }

  /* --------------------------------------------------------------------------
     2. WEATHER / ENVIRONMENT TELEMETRY
     -------------------------------------------------------------------------- */
  function initWeatherTelemetry() {
    async function updateWeather() {
      try {
        const res = await fetch("/api/weather");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const d = await res.json();

        if (d.available === false || d.status === "Unavailable") {
          safeText("weatherCity", d.city || "Local Sensor");
          safeText("weatherTemp", "--°C");
          safeText("weatherStatus", "Telemetry Unavailable");
          safeText("feelsLike", "N/A");
          safeText("windSpeed", "N/A");
          safeText("humidity", "N/A");
          return;
        }

        safeText("weatherCity", d.city || "Local Environment");
        safeText("weatherTemp", d.temperature || "--°C");
        safeText("weatherStatus", d.status || d.description || "Active Monitoring");
        safeText("feelsLike", d.feels_like || "--°C");
        safeText("windSpeed", d.wind || "-- km/h");
        safeText("humidity", d.humidity || "--%");
      } catch (err) {
        console.warn("Weather telemetry fetch failed:", err);
        safeText("weatherCity", "Local Sensor");
        safeText("weatherTemp", "--°C");
        safeText("weatherStatus", "Sensor Offline");
        safeText("feelsLike", "N/A");
        safeText("windSpeed", "N/A");
        safeText("humidity", "N/A");
      }
    }

    updateWeather();
    setInterval(updateWeather, 30000);
  }

  /* --------------------------------------------------------------------------
     3. NETWORK TELEMETRY
     -------------------------------------------------------------------------- */
  function initNetworkTelemetry() {
    async function updateNetwork() {
      try {
        const res = await fetch("/api/network");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const d = await res.json();

        const isOnline = d.connection !== "Offline";
        safeText("netIp", d.ip || "127.0.0.1");
        safeText("netBandwidth", d.bandwidth || "0.0 Mbps");
        safeText("netConnection", d.connection || (isOnline ? "Active" : "Offline"));
        safeText("netWifi", d.wifi || "N/A");

        const statusPill = document.getElementById("netStatusPill");
        const statusText = document.getElementById("netStatusText");
        if (statusText) statusText.textContent = isOnline ? "Synchronized" : "Disconnected";
        if (statusPill) {
          if (isOnline) {
            statusPill.classList.remove("offline");
          } else {
            statusPill.classList.add("offline");
          }
        }
      } catch (err) {
        console.warn("Network telemetry fetch failed:", err);
        safeText("netIp", "N/A");
        safeText("netBandwidth", "--");
        safeText("netConnection", "Offline");
        safeText("netWifi", "N/A");
        const statusText = document.getElementById("netStatusText");
        if (statusText) statusText.textContent = "Offline";
      }
    }

    updateNetwork();
    setInterval(updateNetwork, 5000);
  }

  /* --------------------------------------------------------------------------
     4. CAMERA VISION & VISUAL INPUT
     -------------------------------------------------------------------------- */
  function initCameraControls() {
    const toggle = document.getElementById("cameraToggle");
    const video = document.getElementById("cameraFeed");
    const placeholder = document.getElementById("cameraPlaceholder");
    const liveBadge = document.getElementById("cameraLiveBadge");
    const statusText = document.getElementById("cameraStatusText");

    if (!toggle || !video) return;

    toggle.addEventListener("click", async () => {
      if (!isCameraOn) {
        try {
          cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
          video.srcObject = cameraStream;
          video.style.display = "block";
          if (placeholder) placeholder.style.display = "none";
          if (liveBadge) liveBadge.classList.add("active");
          toggle.classList.add("on");
          if (statusText) {
            statusText.textContent = "ONLINE (LIVE)";
            statusText.style.color = "var(--green)";
          }
          isCameraOn = true;
          if (window.showCyberToast) window.showCyberToast("Optical sensor feed engaged", "success");
        } catch (e) {
          console.error("Camera access denied:", e);
          if (window.showCyberToast) window.showCyberToast("Camera permission denied / sensor unavailable", "error");
          if (statusText) {
            statusText.textContent = "PERMISSION DENIED";
            statusText.style.color = "var(--pink)";
          }
        }
      } else {
        if (cameraStream) {
          cameraStream.getTracks().forEach((track) => track.stop());
        }
        video.srcObject = null;
        video.style.display = "none";
        if (placeholder) placeholder.style.display = "flex";
        if (liveBadge) liveBadge.classList.remove("active");
        toggle.classList.remove("on");
        if (statusText) {
          statusText.textContent = "OFFLINE";
          statusText.style.color = "var(--pink)";
        }
        isCameraOn = false;
      }
    });
  }

  /* --------------------------------------------------------------------------
     5. SPEECH RECOGNITION & SYNTHESIS
     -------------------------------------------------------------------------- */
  function initSpeechRecognition() {
    const mainMicBtn = document.getElementById("mainMicBtn");
    const secondaryMicBtn = document.getElementById("secondaryMicBtn");
    const micStatus = document.getElementById("micStatusLabel");

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      if (micStatus) micStatus.textContent = "SPEECH REC UNAVAILABLE (TYPE COMMANDS BELOW)";
      return;
    }

    recognition = new SpeechRec();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      if (mainMicBtn) mainMicBtn.classList.add("listening");
      if (secondaryMicBtn) secondaryMicBtn.classList.add("listening");
      if (micStatus) micStatus.textContent = "RECEPTOR LISTENING... (SPEAK DIRECTIVE)";
    };

    recognition.onend = () => {
      isListening = false;
      if (mainMicBtn) mainMicBtn.classList.remove("listening");
      if (secondaryMicBtn) secondaryMicBtn.classList.remove("listening");
      if (micStatus) micStatus.textContent = "RECEPTOR READY • TAP CORE OR TYPE BELOW";
    };

    recognition.onerror = (e) => {
      console.warn("Speech recognition error:", e.error);
      isListening = false;
      if (mainMicBtn) mainMicBtn.classList.remove("listening");
      if (secondaryMicBtn) secondaryMicBtn.classList.remove("listening");
      if (micStatus) micStatus.textContent = `MIC STATUS: ${e.error.toUpperCase()}`;
    };

    recognition.onresult = (e) => {
      if (e.results.length > 0) {
        const transcript = e.results[0][0].transcript.trim();
        if (transcript) {
          if (micStatus) micStatus.textContent = `RECEIVED: "${transcript}"`;
          sendChatCommand(transcript, true);
        }
      }
    };

    function toggleSpeech() {
      if (!isListening) {
        try {
          recognition.start();
        } catch (err) {
          console.warn("Recognition start failed:", err);
        }
      } else {
        recognition.stop();
      }
    }

    mainMicBtn?.addEventListener("click", toggleSpeech);
    secondaryMicBtn?.addEventListener("click", toggleSpeech);
  }

  /* --------------------------------------------------------------------------
     6. CHAT PROMPT & TYPEWRITER RESPONSE
     -------------------------------------------------------------------------- */
  function initChatPrompt() {
    const input = document.getElementById("dashboardPromptInput");
    const sendBtn = document.getElementById("dashboardSendBtn");

    function handleSend() {
      const text = (input?.value || "").trim();
      if (!text) return;
      sendChatCommand(text, false);
      if (input) input.value = "";
    }

    sendBtn?.addEventListener("click", handleSend);
    input?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleSend();
    });
  }

  async function sendChatCommand(message, fromMic = false) {
    const responseBox = document.getElementById("aiResponseText");
    const micStatus = document.getElementById("micStatusLabel");
    if (responseBox) responseBox.textContent = "Processing neural instructions...";
    if (micStatus) micStatus.textContent = "AI PROCESSING DIRECTIVE...";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, from_mic: fromMic })
      });

      const data = await res.json().catch(() => ({}));
      const reply = data.response || "Directive executed.";
      typewriterEffect(responseBox, reply);
      speakText(reply);
      if (micStatus) micStatus.textContent = "RECEPTOR READY • TAP CORE OR TYPE BELOW";
    } catch (err) {
      if (responseBox) responseBox.textContent = "Error executing neural instruction.";
      if (micStatus) micStatus.textContent = "RECEPTOR READY • TAP CORE OR TYPE BELOW";
    }
  }

  function typewriterEffect(element, text) {
    if (!element) return;
    element.textContent = "";
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        element.textContent += text.charAt(i);
        i++;
      } else {
        clearInterval(timer);
      }
    }, 20);
  }

  let activeDashboardAudio = null;

  function stopDashboardAudio() {
    if (activeDashboardAudio) {
      try {
        activeDashboardAudio.pause();
        activeDashboardAudio.currentTime = 0;
      } catch (_) {}
      activeDashboardAudio = null;
    }
  }

  async function speakText(text) {
    if (!text || !text.trim()) return;
    stopDashboardAudio();
    console.log("[TTS] dashboard playback requested");

    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok || !data.audio_url) {
        console.warn("[TTS] dashboard backend failed:", data.message || "unknown error");
        return;
      }

      const audioUrl = data.audio_url.startsWith("http") ? data.audio_url : `${window.location.origin}${data.audio_url}`;
      console.log("[TTS] dashboard audio URL:", audioUrl);

      const audio = new Audio(audioUrl);
      activeDashboardAudio = audio;
      audio.volume = 1;

      audio.onplay = () => console.log("[TTS] dashboard audio started");
      audio.onended = () => {
        console.log("[TTS] dashboard audio completed");
        if (activeDashboardAudio === audio) activeDashboardAudio = null;
      };
      audio.onerror = (event) => {
        console.error("[TTS] dashboard audio error:", event);
        if (activeDashboardAudio === audio) activeDashboardAudio = null;
      };

      try {
        await audio.play();
      } catch (playErr) {
        console.warn("[TTS] dashboard autoplay rejected:", playErr);
      }
    } catch (e) {
      console.warn("[TTS] dashboard backend request failed:", e);
    }
  }

  function safeText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function safeWidth(id, val) {
    const el = document.getElementById(id);
    if (el) el.style.width = Math.min(100, Math.max(0, val)) + "%";
  }
})();

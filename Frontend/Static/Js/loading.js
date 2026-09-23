/**
 * SHADOW OS — Futuristic Loading Sequence Controller
 * Simulates diagnostic hardware checks and transitions to /login or /dashboard
 */

(function () {
  "use strict";

  const progressFill = document.getElementById("progressFill");
  const percentText = document.getElementById("percentText");
  const logLine1 = document.getElementById("logLine1");
  const logLine2 = document.getElementById("logLine2");

  const steps = [
    { p: 15, msg1: "INITIALIZING SHADOW KERNEL...", msg2: "Verifying encrypted runtime storage" },
    { p: 35, msg1: "CONNECTING FIRST-LAYER DMM...", msg2: "Loading neural weights and task dispatchers" },
    { p: 60, msg1: "ESTABLISHING PERCEPTUAL MATRIX...", msg2: "Calibrating microphone, speech & camera drivers" },
    { p: 85, msg1: "SECURING OPERATOR ENCLAVE...", msg2: "Checking device tokens and hardware authorization" },
    { p: 100, msg1: "SHADOW OS INITIALIZATION COMPLETE", msg2: "Redirecting to operator authentication..." }
  ];

  let currentStep = 0;
  let progress = 0;

  function updateProgress() {
    if (currentStep >= steps.length) {
      setTimeout(proceedToApp, 600);
      return;
    }

    const target = steps[currentStep].p;
    if (progress < target) {
      progress += Math.floor(Math.random() * 3) + 2;
      if (progress > target) progress = target;

      if (progressFill) progressFill.style.width = progress + "%";
      if (percentText) percentText.textContent = progress + "%";

      if (progress === target) {
        if (logLine1) logLine1.textContent = "✓ " + steps[currentStep].msg1;
        if (logLine2) logLine2.textContent = "» " + steps[currentStep].msg2;
        currentStep++;
      }
    }

    const nextDelay = progress === 100 ? 500 : Math.floor(Math.random() * 40) + 30;
    setTimeout(updateProgress, nextDelay);
  }

  async function proceedToApp() {
    try {
      const res = await fetch("/api/session-status");
      const data = await res.json();
      if (data.logged_in) {
        window.location.href = "/dashboard";
      } else {
        window.location.href = "/login";
      }
    } catch {
      window.location.href = "/login";
    }
  }

  // Start sequence on load
  window.addEventListener("DOMContentLoaded", () => {
    setTimeout(updateProgress, 400);
  });
})();

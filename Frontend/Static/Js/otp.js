/**
 * SHADOW OS — 6-Digit OTP Verification Controller
 * Supports 6-digit box auto-advancement, backspace navigation, paste distribution, countdown timer & verification
 */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const otpInputs = document.querySelectorAll(".otp-digit-input");
    const form = document.getElementById("otpForm");
    const timerDisplay = document.getElementById("otpTimerDisplay");
    const resendBtn = document.getElementById("resendOtpBtn");
    const submitBtn = document.getElementById("otpVerifyBtn");
    const toastEl = document.getElementById("authToast");

    function showToast(msg, isError = false) {
      if (!toastEl) return;
      toastEl.textContent = msg;
      toastEl.className = `auth-toast show ${isError ? "error" : "success"}`;
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => {
        toastEl.className = "auth-toast";
      }, 3000);
    }

    // Auto-focus first digit
    if (otpInputs.length > 0) {
      otpInputs[0].focus();
    }

    // Handle digit input & keyboard navigation
    otpInputs.forEach((input, index) => {
      input.addEventListener("input", (e) => {
        const val = e.target.value;
        // Keep only single numeric digit
        if (val.length > 1) {
          input.value = val.charAt(val.length - 1);
        }

        if (input.value && index < otpInputs.length - 1) {
          otpInputs[index + 1].focus();
        }
      });

      input.addEventListener("keydown", (e) => {
        if (e.key === "Backspace") {
          if (!input.value && index > 0) {
            otpInputs[index - 1].focus();
          }
        } else if (e.key === "ArrowLeft" && index > 0) {
          otpInputs[index - 1].focus();
        } else if (e.key === "ArrowRight" && index < otpInputs.length - 1) {
          otpInputs[index + 1].focus();
        }
      });

      // Handle Paste of 6 digits
      input.addEventListener("paste", (e) => {
        e.preventDefault();
        const pastedData = (e.clipboardData || window.clipboardData).getData("text").trim();
        const digits = pastedData.replace(/\D/g, "").split("");

        if (digits.length > 0) {
          digits.forEach((digit, dIdx) => {
            if (dIdx < otpInputs.length) {
              otpInputs[dIdx].value = digit;
            }
          });
          const nextFocus = Math.min(digits.length, otpInputs.length - 1);
          otpInputs[nextFocus].focus();
        }
      });
    });

    // 5-Minute Countdown Timer
    let totalSeconds = 300;
    function updateTimer() {
      if (totalSeconds <= 0) {
        if (timerDisplay) timerDisplay.textContent = "00:00 (EXPIRED)";
        if (resendBtn) resendBtn.style.pointerEvents = "auto";
        return;
      }
      const m = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
      const s = String(totalSeconds % 60).padStart(2, "0");
      if (timerDisplay) timerDisplay.textContent = `EXPIRES IN: ${m}:${s}`;
      totalSeconds--;
      setTimeout(updateTimer, 1000);
    }
    updateTimer();

    // Resend OTP handler
    if (resendBtn) {
      resendBtn.addEventListener("click", (e) => {
        e.preventDefault();
        showToast("Please log in again to generate a new hardware session OTP.", false);
        setTimeout(() => {
          window.location.href = "/login";
        }, 1500);
      });
    }

    // Submit handler
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();

      let code = "";
      otpInputs.forEach((inp) => {
        code += inp.value.trim();
      });

      if (code.length !== 6) {
        showToast("Please enter all 6 digits of the OTP code", true);
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>VERIFYING CODE...</span>`;

      try {
        const res = await fetch("/api/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code: code })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || !data.success) {
          showToast(data.message || "Invalid OTP code. Please retry.", true);
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span>VERIFY OPERATOR SESSION</span>`;
          return;
        }

        showToast("Session Authorized! Loading Shadow OS Console...", false);
        setTimeout(() => {
          window.location.href = data.redirect || "/dashboard";
        }, 800);
      } catch (err) {
        showToast("Network error verifying session", true);
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>VERIFY OPERATOR SESSION</span>`;
      }
    });
  });
})();

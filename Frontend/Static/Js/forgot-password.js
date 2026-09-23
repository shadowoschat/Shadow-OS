/**
 * SHADOW OS — Password Recovery Controller
 * Handles Multi-step Email verification, OTP confirmation, and New Password setting
 */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const step1 = document.getElementById("recoveryStep1");
    const step2 = document.getElementById("recoveryStep2");
    const form1 = document.getElementById("forgotEmailForm");
    const form2 = document.getElementById("resetPassForm");
    const emailInput = document.getElementById("recoveryEmail");
    const otpInput = document.getElementById("recoveryOtp");
    const newPassInput = document.getElementById("newPassword");
    const confirmPassInput = document.getElementById("confirmNewPassword");
    const submitBtn1 = document.getElementById("sendOtpBtn");
    const submitBtn2 = document.getElementById("resetSubmitBtn");
    const toastEl = document.getElementById("authToast");

    let verifiedEmail = "";

    function showToast(msg, isError = false) {
      if (!toastEl) return;
      toastEl.textContent = msg;
      toastEl.className = `auth-toast show ${isError ? "error" : "success"}`;
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => {
        toastEl.className = "auth-toast";
      }, 3000);
    }

    // Step 1: Request OTP
    form1?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = (emailInput?.value || "").trim().toLowerCase();

      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showToast("Please provide a valid registered email", true);
        return;
      }

      submitBtn1.disabled = true;
      submitBtn1.innerHTML = `<span>GENERATING KEY...</span>`;

      try {
        const res = await fetch("/api/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || !data.success) {
          showToast(data.message || "Failed to generate recovery OTP. Try again.", true);
          submitBtn1.disabled = false;
          submitBtn1.innerHTML = `<span>SEND RECOVERY CODE</span>`;
          return;
        }

        verifiedEmail = email;
        showToast("Recovery code sent to your email!", false);
        step1.style.display = "none";
        step2.style.display = "block";
      } catch (err) {
        showToast("Network error contacting security service", true);
        submitBtn1.disabled = false;
        submitBtn1.innerHTML = `<span>SEND RECOVERY CODE</span>`;
      }
    });

    // Step 2: Reset Password
    form2?.addEventListener("submit", async (e) => {
      e.preventDefault();

      const otp = (otpInput?.value || "").trim();
      const newPass = newPassInput?.value || "";
      const confirmPass = confirmPassInput?.value || "";

      if (!otp || otp.length < 4) {
        showToast("Enter valid recovery OTP code", true);
        return;
      }

      if (newPass.length < 4) {
        showToast("Password must be at least 4 characters", true);
        return;
      }

      if (newPass !== confirmPass) {
        showToast("Passwords do not match", true);
        return;
      }

      submitBtn2.disabled = true;
      submitBtn2.innerHTML = `<span>UPDATING CIPHER...</span>`;

      try {
        const res = await fetch("/api/reset-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: verifiedEmail,
            otp: otp,
            password: newPass
          })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || !data.success) {
          showToast(data.message || "Invalid OTP code or reset failed", true);
          submitBtn2.disabled = false;
          submitBtn2.innerHTML = `<span>UPDATE PASSWORD</span>`;
          return;
        }

        showToast("Password updated successfully! Redirecting to login...", false);
        setTimeout(() => {
          window.location.href = "/login";
        }, 1200);
      } catch (err) {
        showToast("Network error resetting password", true);
        submitBtn2.disabled = false;
        submitBtn2.innerHTML = `<span>UPDATE PASSWORD</span>`;
      }
    });
  });
})();

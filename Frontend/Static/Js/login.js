/**
 * SHADOW OS — Login Authentication Controller
 * Handles credentials validation, password visibility, server integration & redirect
 */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const idInput = document.getElementById("loginIdentifier");
    const passInput = document.getElementById("loginPassword");
    const toggleBtn = document.getElementById("togglePassword");
    const idError = document.getElementById("idError");
    const passError = document.getElementById("passError");
    const submitBtn = document.getElementById("loginSubmitBtn");
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

    // Toggle Password Visibility
    if (toggleBtn && passInput) {
      toggleBtn.addEventListener("click", () => {
        const isPass = passInput.type === "password";
        passInput.type = isPass ? "text" : "password";
        toggleBtn.textContent = isPass ? "HIDE" : "SHOW";
      });
    }

    // Clear error on input
    idInput?.addEventListener("input", () => { idError.textContent = ""; });
    passInput?.addEventListener("input", () => { passError.textContent = ""; });

    // Submit handler
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      const identifier = (idInput?.value || "").trim();
      const password = passInput?.value || "";

      let valid = true;
      if (!identifier) {
        idError.textContent = "Identifier is required";
        valid = false;
      }
      if (!password) {
        passError.textContent = "Password is required";
        valid = false;
      }

      if (!valid) return;

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>VERIFYING...</span>`;

      try {
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: identifier, password: password })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || !data.success) {
          showToast(data.message || " ", true);
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span>ACCESS TERMINAL</span>`;
          return;
        }

        if (data.needs_otp) {
          showToast("OTP generated. Enter verification code.", false);
          setTimeout(() => {
            window.location.href = data.redirect || "/otp";
          }, 600);
        } else {
          showToast("Access Granted. Initializing Shadow OS...", false);
          setTimeout(() => {
            window.location.href = data.redirect || "/dashboard";
          }, 600);
        }
      } catch (err) {
        showToast("Network error connecting to Shadow Core", true);
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>ACCESS TERMINAL</span>`;
      }
    });
  });
})();

/**
 * SHADOW OS — Signup & Identity Creation Controller
 * Dynamic username suggestion, real-time password strength scoring & API signup integration
 */

(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("signupForm");
    const firstName = document.getElementById("suFirstName");
    const lastName = document.getElementById("suLastName");
    const email = document.getElementById("suEmail");
    const username = document.getElementById("suUsername");
    const password = document.getElementById("suPassword");
    const confirm = document.getElementById("suConfirm");
    const strengthBar = document.getElementById("strengthBar");
    const strengthText = document.getElementById("strengthText");
    const terms = document.getElementById("suTerms");
    const submitBtn = document.getElementById("signupSubmitBtn");
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

    // Auto-generate username from first & last name
    function updateUsername() {
      const f = (firstName?.value || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
      const l = (lastName?.value || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
      if (username && (!username.dataset.touched || !username.value)) {
        username.value = f && l ? `${f}_${l}` : f || l;
      }
    }

    firstName?.addEventListener("input", updateUsername);
    lastName?.addEventListener("input", updateUsername);
    username?.addEventListener("input", () => {
      username.dataset.touched = "true";
    });

    // Password strength score
    function scorePassword(p) {
      if (!p) return 0;
      let score = 0;
      if (p.length >= 8) score++;
      if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++;
      if (/\d/.test(p)) score++;
      if (/[^A-Za-z0-9]/.test(p)) score++;
      return score;
    }

    password?.addEventListener("input", () => {
      const p = password.value;
      const score = scorePassword(p);
      const levels = [
        { w: "0%", c: "transparent", t: "STRENGTH" },
        { w: "25%", c: "#ff0055", t: "WEAK" },
        { w: "50%", c: "#ffaa00", t: "MEDIUM" },
        { w: "75%", c: "#00eaff", t: "STRONG" },
        { w: "100%", c: "#00ff9d", t: "CYBER SECURE" }
      ];

      const lvl = levels[score];
      if (strengthBar) {
        strengthBar.style.width = lvl.w;
        strengthBar.style.backgroundColor = lvl.c;
      }
      if (strengthText) {
        strengthText.textContent = lvl.t;
        strengthText.style.color = lvl.c;
      }
    });

    // Form submit
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();

      const f = (firstName?.value || "").trim();
      const l = (lastName?.value || "").trim();
      const em = (email?.value || "").trim().toLowerCase();
      const un = (username?.value || "").trim();
      const pw = password?.value || "";
      const cp = confirm?.value || "";

      if (!f || !l || !em || !un || !pw || !cp) {
        showToast("All fields are required", true);
        return;
      }

      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
        showToast("Please enter a valid email address", true);
        return;
      }

      if (pw !== cp) {
        showToast("Passwords do not match", true);
        return;
      }

      if (pw.length < 4) {
        showToast("Password must be at least 4 characters", true);
        return;
      }

      if (terms && !terms.checked) {
        showToast("You must accept the Shadow OS terms", true);
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>CREATING IDENTITY...</span>`;

      try {
        const res = await fetch("/api/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            first: f,
            last: l,
            email: em,
            username: un,
            password: pw
          })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || !data.success) {
          showToast(data.message || "Signup failed. Try a different username/email.", true);
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span>CREATE OPERATOR IDENTITY</span>`;
          return;
        }

        showToast(data.message || "Identity Registered! Please check your email to verify your account.", false);
        setTimeout(() => {
          window.location.href = data.redirect || "/login";
        }, 3000);
      } catch (err) {
        showToast("Network error during identity registration", true);
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>CREATE OPERATOR IDENTITY</span>`;
      }
    });
  });
})();

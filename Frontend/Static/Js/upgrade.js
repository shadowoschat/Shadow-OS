/**
 * SHADOW OS — Upgrade Matrix Controller
 * Billing cycle toggle + checkout modal interaction
 */

(function () {
  "use strict";

  const PLANS = {
    core:     { monthly: 0,  annual: 0  },
    cyber:    { monthly: 19, annual: 15 },
    sovereign:{ monthly: 49, annual: 39 }
  };

  let isAnnual = false;

  const billingToggle = document.getElementById("billingToggle");
  billingToggle?.addEventListener("change", () => {
    isAnnual = billingToggle.checked;
    updatePrices();
  });

  function updatePrices() {
    Object.entries(PLANS).forEach(([key, prices]) => {
      const el    = document.getElementById(`price-${key}`);
      const price = isAnnual ? prices.annual : prices.monthly;
      if (el) el.textContent = price === 0 ? "FREE" : `\$${price}`;
    });

    const billingLabel = document.getElementById("billingPeriodLabel");
    if (billingLabel) billingLabel.textContent = isAnnual ? "/mo (billed annually)" : "/mo";
  }

  /* ── Checkout modal ─────────────────────────────────────────────────── */
  function openCheckoutModal(plan) {
    const modal     = document.getElementById("checkoutModal");
    const planNameEl = document.getElementById("checkoutPlanName");
    const priceEl   = document.getElementById("checkoutPrice");

    if (planNameEl) planNameEl.textContent = plan.name;
    if (priceEl) {
      const price = isAnnual ? PLANS[plan.key].annual : PLANS[plan.key].monthly;
      priceEl.textContent = price === 0 ? "FREE" : `\$${price}/mo`;
    }

    modal?.classList.add("active");
  }

  document.getElementById("checkoutModalClose")?.addEventListener("click", () => {
    document.getElementById("checkoutModal")?.classList.remove("active");
  });

  document.getElementById("checkoutModal")?.addEventListener("click", (e) => {
    if (e.target === document.getElementById("checkoutModal"))
      document.getElementById("checkoutModal")?.classList.remove("active");
  });

  document.getElementById("checkoutConfirmBtn")?.addEventListener("click", () => {
    if (window.showCyberToast) window.showCyberToast("Upgrade processing — payment gateway coming soon!", "info");
    document.getElementById("checkoutModal")?.classList.remove("active");
  });

  /* ── Attach plan buttons ────────────────────────────────────────────── */
  [
    { key: "core",      name: "Operator Core",       free: true },
    { key: "cyber",     name: "Cyber Architect",     free: false },
    { key: "sovereign", name: "Shadow Sovereign",    free: false }
  ].forEach(plan => {
    document.getElementById(`upgrade-btn-${plan.key}`)?.addEventListener("click", () => {
      if (plan.free) {
        if (window.showCyberToast) window.showCyberToast("You are already on the Operator Core tier", "info");
        return;
      }
      openCheckoutModal(plan);
    });
  });
})();

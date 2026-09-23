/**
 * SHADOW OS — AI Image Studio Controller
 * Centered Generation Loading Panel + Futuristic Animated HUD +
 * Showcase Controls + Image Library Modal + Lightbox Zoom
 */

(function () {
  "use strict";

  let allImagesCache = [];
  let selectedLibraryImage = null;

  document.addEventListener("DOMContentLoaded", () => {
    initImageGenerator();
    loadGalleryImages();
    initLibraryModal();
    initLightbox();

    const refreshBtn = document.getElementById("refreshGalleryBtn");
    refreshBtn?.addEventListener("click", () => {
      loadGalleryImages();
      if (window.showCyberToast) window.showCyberToast("Gallery synchronized", "info");
    });
  });

  /* --------------------------------------------------------------------------
     1. IMAGE GENERATOR (STEP 1 -> STEP 2 -> STEP 3 -> STEP 4)
     -------------------------------------------------------------------------- */
  function initImageGenerator() {
    const promptInput = document.getElementById("imagePromptInput");
    const styleSelect = document.getElementById("artStyleSelect");
    const aspectSelect = document.getElementById("aspectRatioSelect");
    const generateBtn = document.getElementById("generateArtworkBtn");

    const genPanel = document.getElementById("generationPanel");
    const genLoading = document.getElementById("generationLoading");
    const genOutput = document.getElementById("generationOutput");
    const genStatusSub = document.getElementById("generationStatusSub");
    const displayImg = document.getElementById("generatedImageDisplay");
    const showcaseDownload = document.getElementById("showcaseDownloadBtn");
    const showcaseView = document.getElementById("showcaseViewBtn");
    const showcaseClose = document.getElementById("showcaseCloseBtn");

    showcaseClose?.addEventListener("click", () => {
      if (genPanel) genPanel.classList.remove("active");
    });

    generateBtn?.addEventListener("click", async () => {
      const rawPrompt = (promptInput?.value || "").trim();
      if (!rawPrompt) {
        if (window.showCyberToast) window.showCyberToast("Please describe the image to synthesize", "error");
        return;
      }

      const style = styleSelect?.value || "Cyberpunk Neon";
      const aspect = aspectSelect?.value || "1:1";
      const fullPrompt = `${rawPrompt} in ${style} style, aspect ${aspect}`;

      // STEP 1: Show centered IMAGE GENERATION loading/processing panel
      if (genPanel) genPanel.classList.add("active");
      if (genLoading) genLoading.style.display = "flex";
      if (genOutput) genOutput.classList.remove("active");

      generateBtn.disabled = true;
      generateBtn.innerHTML = `<span>SYNTHESIZING...</span>`;
      if (window.showCyberToast) window.showCyberToast("Synthesis job submitted to Neural Engine", "info");

      // STEP 2: Futuristic animated generation effect states
      if (genStatusSub) genStatusSub.textContent = "Connecting to high-dimensional latent space...";
      setTimeout(() => {
        if (genStatusSub) genStatusSub.textContent = "Sampling denoising diffusion steps & rendering 4K tensors...";
      }, 1500);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: `generate image ${fullPrompt}` })
        });

        const data = await res.json().catch(() => ({}));
        
        // Wait a short moment for file write, then find newest image
        setTimeout(async () => {
          const imgRes = await fetch("/api/images");
          const images = await imgRes.json().catch(() => []);
          const latestImg = images && images.length > 0 ? images[0] : null;

          // STEP 3: Replace loading area with generated image & controls
          if (genLoading) genLoading.style.display = "none";
          if (genOutput) genOutput.classList.add("active");

          if (latestImg && displayImg) {
            displayImg.src = latestImg.url;
            displayImg.alt = latestImg.name;

            if (showcaseDownload) {
              showcaseDownload.href = latestImg.url;
              showcaseDownload.download = latestImg.name;
            }

            if (showcaseView) {
              showcaseView.onclick = () => openLightbox(latestImg.url, latestImg.name);
            }
          }

          // STEP 4: Update gallery and library
          loadGalleryImages();
          if (window.showCyberToast) window.showCyberToast("Neural image generation complete!", "success");

          generateBtn.disabled = false;
          generateBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
            <span>GENERATE ARTWORK</span>
          `;
        }, 3200);

      } catch (err) {
        if (genLoading) genLoading.style.display = "none";
        if (genPanel) genPanel.classList.remove("active");
        if (window.showCyberToast) window.showCyberToast("Neural Engine connection timed out", "error");
        generateBtn.disabled = false;
        generateBtn.innerHTML = `<span>GENERATE ARTWORK</span>`;
      }
    });
  }

  /* --------------------------------------------------------------------------
     2. GALLERY LOADING
     -------------------------------------------------------------------------- */
  async function loadGalleryImages() {
    const galleryGrid = document.getElementById("galleryGrid");
    if (!galleryGrid) return;

    try {
      const res = await fetch("/api/images");
      if (!res.ok) throw new Error("Failed to fetch images");
      const images = await res.json();
      allImagesCache = images || [];

      galleryGrid.innerHTML = "";

      if (allImagesCache.length === 0) {
        galleryGrid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color: var(--text-muted); font-family: var(--font-mono); font-size: 0.8rem;">
            NO NEURAL ARTWORKS FOUND • ENTER PROMPT ABOVE TO SYNTHESIZE
          </div>
        `;
        return;
      }

      allImagesCache.forEach((img) => {
        const card = document.createElement("div");
        card.className = "image-card";
        card.innerHTML = `
          <div class="image-thumbnail-wrap">
            <img src="${img.url}" alt="${img.name}" loading="lazy" />
          </div>
          <div class="image-card-info">
            <span class="image-card-title" title="${img.name}">${img.name}</span>
            <div class="image-card-actions">
              <button class="btn-cyber btn-cyber-icon btn-view" title="View Fullscreen" style="width:28px;height:28px;padding:3px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
              <a href="${img.url}" download="${img.name}" class="btn-cyber btn-cyber-icon" title="Download Image" style="width:28px;height:28px;padding:3px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              </a>
            </div>
          </div>
        `;

        card.querySelector(".btn-view")?.addEventListener("click", () => {
          openLightbox(img.url, img.name);
        });

        galleryGrid.appendChild(card);
      });
    } catch (err) {
      console.warn("Could not load gallery:", err);
    }
  }

  /* --------------------------------------------------------------------------
     3. IMAGE LIBRARY MODAL INTERFACE
     -------------------------------------------------------------------------- */
  function initLibraryModal() {
    const openBtn = document.getElementById("openLibraryBtn");
    const closeBtn = document.getElementById("closeLibraryBtn");
    const modal = document.getElementById("libraryModal");
    const searchInput = document.getElementById("librarySearchInput");
    const grid = document.getElementById("libraryGrid");

    if (!modal) return;

    function renderLibrary(filterText = "") {
      if (!grid) return;
      grid.innerHTML = "";

      const filtered = allImagesCache.filter(img => 
        img.name.toLowerCase().includes(filterText.toLowerCase())
      );

      if (filtered.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 30px; font-family: var(--font-mono);">NO MATCHING ARTWORKS FOUND</div>`;
        return;
      }

      filtered.forEach(img => {
        const item = document.createElement("div");
        item.className = "library-thumb-card";
        item.innerHTML = `
          <img src="${img.url}" alt="${img.name}" loading="lazy" />
          <div class="library-thumb-title">${img.name}</div>
        `;

        item.addEventListener("click", () => {
          selectedLibraryImage = img;
          document.querySelectorAll(".library-thumb-card").forEach(el => el.classList.remove("selected"));
          item.classList.add("selected");
          modal.classList.remove("active");
          openLightbox(img.url, img.name);
        });

        grid.appendChild(item);
      });
    }

    openBtn?.addEventListener("click", () => {
      modal.classList.add("active");
      renderLibrary(searchInput?.value || "");
    });

    closeBtn?.addEventListener("click", () => {
      modal.classList.remove("active");
    });

    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });

    searchInput?.addEventListener("input", () => {
      renderLibrary(searchInput.value.trim());
    });
  }

  /* --------------------------------------------------------------------------
     4. LIGHTBOX MODAL
     -------------------------------------------------------------------------- */
  function initLightbox() {
    const lightbox = document.getElementById("imageLightbox");
    const closeBtn = document.getElementById("lightboxCloseBtn");

    closeBtn?.addEventListener("click", () => {
      if (lightbox) lightbox.classList.remove("active");
    });

    lightbox?.addEventListener("click", (e) => {
      if (e.target === lightbox) lightbox.classList.remove("active");
    });
  }

  function openLightbox(imgUrl, imgTitle) {
    const lightbox = document.getElementById("imageLightbox");
    const imgEl = document.getElementById("lightboxImg");
    const titleEl = document.getElementById("lightboxTitle");
    const downloadEl = document.getElementById("lightboxDownloadBtn");

    if (imgEl) imgEl.src = imgUrl;
    if (titleEl) titleEl.textContent = imgTitle;
    if (downloadEl) {
      downloadEl.href = imgUrl;
      downloadEl.download = imgTitle;
    }

    if (lightbox) lightbox.classList.add("active");
  }
})();

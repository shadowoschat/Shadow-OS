/* ==========================================================================
   SHADOW OS — Music Player Controller
   Handles: track data, carousels, now playing, up next queue,
           bottom player dock, visualizer, playback sync, voice search
   ========================================================================== */

(function () {
  'use strict';

  /* ---------------- TRACK LIBRARY ---------------- */
  const TRACK_LIBRARY = [
    { id: 1, title: 'Neural Resonance', artist: 'Shadow Synthwave Collective', album: 'Cyber Dreams', duration: '04:32', durationSec: 272, artwork: 'https://images.pexels.com/photos/426976/pexels-photo-426976.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 2, title: 'Ghost Protocol', artist: 'Datastream', album: 'Neon Grid', duration: '03:45', durationSec: 225, artwork: 'https://images.pexels.com/photos/18197120/pexels-photo-18197120.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 3, title: 'Chrome Lullaby', artist: 'Vapor Angel', album: 'Liquid Metal', duration: '05:12', durationSec: 312, artwork: 'https://images.pexels.com/photos/12089403/pexels-photo-12089403.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 4, title: 'Midnight Protocol', artist: 'Null Pointer', album: 'System Override', duration: '03:28', durationSec: 208, artwork: 'https://images.pexels.com/photos/35849147/pexels-photo-35849147.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 5, title: 'Holographic Love', artist: 'Synthwave Society', album: 'Future Past', duration: '04:15', durationSec: 255, artwork: 'https://images.pexels.com/photos/18076561/pexels-photo-18076561.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 6, title: 'Electric Mirage', artist: 'Circuit Breaker', album: 'Voltage', duration: '03:52', durationSec: 232, artwork: 'https://images.pexels.com/photos/33418887/pexels-photo-33418887.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 7, title: 'Quantum Drift', artist: 'The Binary Collective', album: 'Wave Function', duration: '06:08', durationSec: 368, artwork: 'https://images.pexels.com/photos/8699994/pexels-photo-8699994.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 8, title: 'Pixel Storm', artist: 'Glitch Theory', album: 'Corrupted Data', duration: '04:01', durationSec: 241, artwork: 'https://images.pexels.com/photos/18069858/pexels-photo-18069858.png?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 9, title: 'Neon Cathedral', artist: 'Digital Monk', album: 'Sacred Circuits', duration: '05:30', durationSec: 330, artwork: 'https://images.pexels.com/photos/8659276/pexels-photo-8659276.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 10, title: 'Void Walker', artist: 'Static Pulse', album: 'Dark Matter', duration: '03:38', durationSec: 218, artwork: 'https://images.pexels.com/photos/4793492/pexels-photo-4793492.png?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 11, title: 'Synthetic Dawn', artist: 'AI Orchestra', album: 'Machine Learning', duration: '04:45', durationSec: 285, artwork: 'https://images.pexels.com/photos/33418888/pexels-photo-33418888.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
    { id: 12, title: 'Crimson Override', artist: 'Red Circuit', album: 'System Failure', duration: '03:55', durationSec: 235, artwork: 'https://images.pexels.com/photos/6842724/pexels-photo-6842724.jpeg?auto=compress&cs=tinysrgb&h=350&w=350' },
  ];

  /* ---------------- STATE ---------------- */
  let currentTrackIndex = 0;
  let isPlaying = false;
  let progressInterval = null;
  let currentProgress = 0;       // seconds
  let shuffleMode = false;
  let loopMode = false;
  let volume = 70;
  let isMuted = false;
  let favorites = new Set();
  let queue = [];
  let heroIndex = 0;

  const HERO_TRACKS = [TRACK_LIBRARY[0], TRACK_LIBRARY[6], TRACK_LIBRARY[10]];

  /* ---------------- DOM SHORTCUTS ---------------- */
  const $ = (id) => document.getElementById(id);
  const playIcon = '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
  const pauseIcon = '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
  const playIconSm = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
  const pauseIconSm = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';

  /* ---------------- AUDIO ENGINE ---------------- */
  const audioPlayer = new Audio();

  /* ---------------- INIT ---------------- */
  document.addEventListener('DOMContentLoaded', () => {
    buildHeroPagination();
    renderTrendingCarousel();
    renderRecentCarousel();
    renderQueue();
    loadTrack(0, false);
    bindControls();
    bindCarousels();
    bindSearch();
    bindVoiceSearch();
    bindSubSidebar();
    startVisualizer();
    startClock();
    initAudioPlayer();
    fetchServerSongs();
  });

  function initAudioPlayer() {
    audioPlayer.addEventListener('timeupdate', () => {
      if (audioPlayer.duration && !isNaN(audioPlayer.duration)) {
        currentProgress = Math.floor(audioPlayer.currentTime);
        const track = TRACK_LIBRARY[currentTrackIndex];
        if (track) {
          track.durationSec = Math.floor(audioPlayer.duration);
          track.duration = formatTime(track.durationSec);
          if ($('totalTime')) $('totalTime').textContent = track.duration;
          if ($('bpTotalTime')) $('bpTotalTime').textContent = track.duration;
          if ($('scrubBar')) $('scrubBar').max = track.durationSec;
          if ($('bpScrubBar')) $('bpScrubBar').max = track.durationSec;
        }
        updateProgressUI();
      }
    });

    audioPlayer.addEventListener('ended', () => {
      if (loopMode) {
        audioPlayer.currentTime = 0;
        audioPlayer.play().catch(() => {});
      } else {
        nextTrack();
      }
    });
  }

  async function fetchServerSongs() {
    try {
      const res = await fetch('/api/songs');
      if (res.ok) {
        const serverSongs = await res.json();
        if (Array.isArray(serverSongs) && serverSongs.length > 0) {
          serverSongs.forEach((s, idx) => {
            TRACK_LIBRARY.unshift({
              id: 'srv_' + idx,
              title: s.name.replace(/\.[^/.]+$/, ""),
              artist: 'Local Neural Vault',
              album: 'Shadow Audio Library',
              duration: '03:30',
              durationSec: 210,
              audioUrl: s.url,
              artwork: 'https://images.pexels.com/photos/18197120/pexels-photo-18197120.jpeg?auto=compress&cs=tinysrgb&h=350&w=350'
            });
          });
          renderTrendingCarousel();
          renderRecentCarousel();
          renderQueue();
          loadTrack(0, false);
        }
      }
    } catch (e) {
      console.warn("Could not load server songs:", e);
    }
  }

  /* ---------------- HERO BANNER ---------------- */
  function buildHeroPagination() {
    const container = $('heroPagination');
    if (!container) return;
    container.innerHTML = '';
    HERO_TRACKS.forEach((_, i) => {
      const dot = document.createElement('span');
      dot.className = 'hero-dot' + (i === heroIndex ? ' active' : '');
      dot.addEventListener('click', () => {
        heroIndex = i;
        updateHeroBanner();
      });
      container.appendChild(dot);
    });
  }

  function updateHeroBanner() {
    const track = HERO_TRACKS[heroIndex];
    if (!track) return;
    $('heroTitle').textContent = track.title;
    $('heroArtist').textContent = track.artist;
    document.querySelectorAll('.hero-dot').forEach((d, i) => {
      d.classList.toggle('active', i === heroIndex);
    });
  }

  function bindHeroPlay() {
    const btn = $('heroPlayBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
      const track = HERO_TRACKS[heroIndex];
      const libIndex = TRACK_LIBRARY.findIndex(t => t.id === track.id);
      if (libIndex >= 0) {
        loadTrack(libIndex, true);
      }
    });
  }

  /* ---------------- CAROUSELS ---------------- */
  function renderTrendingCarousel() {
    const container = $('trendingScroll');
    if (!container) return;
    const trending = TRACK_LIBRARY.slice(0, 6);
    container.innerHTML = '';
    trending.forEach((track, i) => {
      container.appendChild(createTrackCard(track, i));
    });
  }

  function renderRecentCarousel() {
    const container = $('recentScroll');
    if (!container) return;
    const recent = [...TRACK_LIBRARY].slice(6, 12).reverse();
    container.innerHTML = '';
    recent.forEach((track, i) => {
      container.appendChild(createTrackCard(track, i));
    });
  }

  function createTrackCard(track, index) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.innerHTML = `
      <div class="track-card-artwork">
        <img src="${track.artwork}" alt="${track.title}" loading="lazy" />
        <div class="track-card-overlay">
          <div class="track-card-play">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          </div>
        </div>
      </div>
      <div class="track-card-title">${track.title}</div>
      <div class="track-card-artist">${track.artist}</div>
    `;
    card.addEventListener('click', () => {
      const libIndex = TRACK_LIBRARY.findIndex(t => t.id === track.id);
      if (libIndex >= 0) loadTrack(libIndex, true);
    });
    return card;
  }

  function bindCarousels() {
    document.querySelectorAll('.carousel-arrow').forEach(arrow => {
      arrow.addEventListener('click', () => {
        const targetId = arrow.dataset.target;
        const track = $(targetId);
        if (!track) return;
        const scrollAmount = 340;
        if (arrow.dataset.dir === 'left') {
          track.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        } else {
          track.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        }
      });
    });
  }

  /* ---------------- QUEUE / UP NEXT ---------------- */
  function renderQueue() {
    const container = $('playlistItems');
    if (!container) return;
    queue = TRACK_LIBRARY.slice(1);
    container.innerHTML = '';
    if (queue.length === 0) {
      container.innerHTML = '<p class="un-empty">Queue is empty</p>';
      return;
    }
    queue.forEach((track, i) => {
      const item = document.createElement('div');
      item.className = 'queue-item';
      item.innerHTML = `
        <div class="queue-item-thumb">
          <img src="${track.artwork}" alt="${track.title}" loading="lazy" />
        </div>
        <div class="queue-item-info">
          <span class="queue-item-title">${track.title}</span>
          <span class="queue-item-artist">${track.artist}</span>
        </div>
        <span class="queue-item-duration">${track.duration}</span>
        <div class="queue-item-options">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="1.5"></circle><circle cx="12" cy="5" r="1.5"></circle><circle cx="12" cy="19" r="1.5"></circle></svg>
        </div>
      `;
      item.addEventListener('click', () => {
        const libIndex = TRACK_LIBRARY.findIndex(t => t.id === track.id);
        if (libIndex >= 0) loadTrack(libIndex, true);
      });
      container.appendChild(item);
    });
  }

  function highlightCurrentQueue() {
    const items = document.querySelectorAll('.queue-item');
    items.forEach((item, i) => {
      item.classList.toggle('now-playing', queue[i] && queue[i].id === TRACK_LIBRARY[currentTrackIndex].id);
    });
  }

  /* ---------------- TRACK LOADING ---------------- */
  function loadTrack(index, autoPlay) {
    if (index < 0 || index >= TRACK_LIBRARY.length) return;
    currentTrackIndex = index;
    currentProgress = 0;
    const track = TRACK_LIBRARY[index];

    // Now Playing panel
    $('npArtwork').src = track.artwork;
    $('trackTitle').textContent = track.title.toUpperCase();
    $('trackArtist').textContent = track.artist;
    $('currentTime').textContent = '00:00';
    $('totalTime').textContent = track.duration;
    $('scrubBar').value = 0;
    $('scrubBar').max = track.durationSec;

    // Bottom dock
    $('bpArtwork').src = track.artwork;
    $('bpTitle').textContent = track.title;
    $('bpArtist').textContent = track.artist;
    $('bpCurrentTime').textContent = '00:00';
    $('bpTotalTime').textContent = track.duration;
    $('bpScrubBar').value = 0;
    $('bpScrubBar').max = track.durationSec;

    // Favorite state
    updateFavoriteBtn();

    highlightCurrentQueue();

    if (autoPlay) {
      play();
    } else {
      pause();
    }
  }

  /* ---------------- PLAYBACK CONTROL ---------------- */
  function play() {
    isPlaying = true;
    updatePlayButtons();
    $('heroVinyl')?.classList.add('spinning');
    const track = TRACK_LIBRARY[currentTrackIndex];
    if (track && track.audioUrl) {
      if (!audioPlayer.src.endsWith(track.audioUrl)) {
        audioPlayer.src = track.audioUrl;
      }
      audioPlayer.play().catch(() => {});
    } else {
      startProgress();
    }
  }

  function pause() {
    isPlaying = false;
    updatePlayButtons();
    $('heroVinyl')?.classList.remove('spinning');
    audioPlayer.pause();
    stopProgress();
  }

  function togglePlay() {
    if (isPlaying) pause();
    else play();
  }

  function updatePlayButtons() {
    const npBtn = $('playPauseBtn');
    const bpBtn = $('bpPlayPauseBtn');
    const heroBtn = $('heroPlayBtn');
    if (isPlaying) {
      if (npBtn) npBtn.innerHTML = pauseIcon;
      if (bpBtn) bpBtn.innerHTML = pauseIconSm;
      if (heroBtn) {
        heroBtn.innerHTML = `${pauseIcon}<span>PAUSE</span>`;
      }
    } else {
      if (npBtn) npBtn.innerHTML = playIcon;
      if (bpBtn) bpBtn.innerHTML = playIconSm;
      if (heroBtn) {
        heroBtn.innerHTML = `${playIcon}<span>PLAY</span>`;
      }
    }
  }

  function nextTrack() {
    if (shuffleMode) {
      let randomIndex;
      do {
        randomIndex = Math.floor(Math.random() * TRACK_LIBRARY.length);
      } while (randomIndex === currentTrackIndex && TRACK_LIBRARY.length > 1);
      loadTrack(randomIndex, isPlaying);
    } else {
      loadTrack((currentTrackIndex + 1) % TRACK_LIBRARY.length, isPlaying);
    }
  }

  function prevTrack() {
    if (currentProgress > 3) {
      currentProgress = 0;
      updateProgressUI();
      return;
    }
    loadTrack((currentTrackIndex - 1 + TRACK_LIBRARY.length) % TRACK_LIBRARY.length, isPlaying);
  }

  /* ---------------- PROGRESS SIMULATION ---------------- */
  function startProgress() {
    stopProgress();
    progressInterval = setInterval(() => {
      currentProgress += 1;
      const track = TRACK_LIBRARY[currentTrackIndex];
      if (currentProgress >= track.durationSec) {
        if (loopMode) {
          currentProgress = 0;
        } else {
          stopProgress();
          nextTrack();
          return;
        }
      }
      updateProgressUI();
    }, 1000);
  }

  function stopProgress() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }

  function updateProgressUI() {
    const track = TRACK_LIBRARY[currentTrackIndex];
    const pct = (currentProgress / track.durationSec) * 100;
    const timeStr = formatTime(currentProgress);

    $('currentTime').textContent = timeStr;
    $('bpCurrentTime').textContent = timeStr;
    $('scrubBar').value = currentProgress;
    $('bpScrubBar').value = currentProgress;
  }

  function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  /* ---------------- FAVORITE ---------------- */
  function toggleFavorite() {
    const track = TRACK_LIBRARY[currentTrackIndex];
    if (favorites.has(track.id)) {
      favorites.delete(track.id);
    } else {
      favorites.add(track.id);
    }
    updateFavoriteBtn();
  }

  function updateFavoriteBtn() {
    const btn = $('npFavoriteBtn');
    if (!btn) return;
    const track = TRACK_LIBRARY[currentTrackIndex];
    btn.classList.toggle('favorited', favorites.has(track.id));
  }

  /* ---------------- SHUFFLE / LOOP ---------------- */
  function toggleShuffle() {
    shuffleMode = !shuffleMode;
    $('shuffleBtn')?.classList.toggle('active', shuffleMode);
    $('bpShuffleBtn')?.classList.toggle('active', shuffleMode);
  }

  function toggleLoop() {
    loopMode = !loopMode;
    $('loopBtn')?.classList.toggle('active', loopMode);
    $('bpRepeatBtn')?.classList.toggle('active', loopMode);
  }

  /* ---------------- VOLUME ---------------- */
  function setVolume(val) {
    volume = parseInt(val);
    isMuted = volume === 0;
    updateMuteIcon();
  }

  function toggleMute() {
    isMuted = !isMuted;
    const slider = $('volumeSlider');
    if (isMuted) {
      slider.dataset.prevVal = slider.value;
      slider.value = 0;
    } else {
      slider.value = slider.dataset.prevVal || 70;
    }
    updateMuteIcon();
  }

  function updateMuteIcon() {
    const btn = $('bpMuteBtn');
    if (!btn) return;
    if (isMuted) {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`;
    } else {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>`;
    }
  }

  /* ---------------- CLEAR QUEUE ---------------- */
  function clearQueue() {
    queue = [];
    const container = $('playlistItems');
    if (container) {
      container.innerHTML = '<p class="un-empty">Queue cleared</p>';
    }
  }

  /* ---------------- BIND ALL CONTROLS ---------------- */
  function bindControls() {
    bindHeroPlay();

    // Now Playing panel controls
    $('playPauseBtn')?.addEventListener('click', togglePlay);
    $('prevBtn')?.addEventListener('click', prevTrack);
    $('nextBtn')?.addEventListener('click', nextTrack);
    $('shuffleBtn')?.addEventListener('click', toggleShuffle);
    $('loopBtn')?.addEventListener('click', toggleLoop);
    $('npFavoriteBtn')?.addEventListener('click', toggleFavorite);

    // Scrubber (now playing)
    $('scrubBar')?.addEventListener('input', (e) => {
      currentProgress = parseInt(e.target.value);
      updateProgressUI();
    });

    // Bottom dock controls
    $('bpPlayPauseBtn')?.addEventListener('click', togglePlay);
    $('bpPrevBtn')?.addEventListener('click', prevTrack);
    $('bpNextBtn')?.addEventListener('click', nextTrack);
    $('bpShuffleBtn')?.addEventListener('click', toggleShuffle);
    $('bpRepeatBtn')?.addEventListener('click', toggleLoop);
    $('bpMuteBtn')?.addEventListener('click', toggleMute);

    // Bottom scrubber
    $('bpScrubBar')?.addEventListener('input', (e) => {
      currentProgress = parseInt(e.target.value);
      updateProgressUI();
    });

    // Volume
    $('volumeSlider')?.addEventListener('input', (e) => setVolume(e.target.value));

    // Queue toggle (scroll to right sidebar on mobile)
    $('bpQueueToggleBtn')?.addEventListener('click', () => {
      const rs = document.querySelector('.music-rightsidebar');
      if (rs) {
        rs.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });

    // Clear queue
    $('clearQueueBtn')?.addEventListener('click', clearQueue);
  }

  /* ---------------- SEARCH ---------------- */
  function bindSearch() {
    const input = $('globalSearchInput');
    const dropdown = $('searchResultsDropdown');
    if (!input || !dropdown) return;

    input.addEventListener('input', () => {
      const query = input.value.trim().toLowerCase();
      if (query.length < 2) {
        dropdown.style.display = 'none';
        return;
      }
      const results = TRACK_LIBRARY.filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.artist.toLowerCase().includes(query) ||
        t.album.toLowerCase().includes(query)
      );
      if (results.length === 0) {
        dropdown.innerHTML = '<div class="search-no-results">No tracks found</div>';
      } else {
        dropdown.innerHTML = results.map(t => `
          <div class="search-result-item" data-id="${t.id}">
            <img src="${t.artwork}" alt="${t.title}" />
            <div class="search-result-info">
              <span class="search-result-title">${t.title}</span>
              <span class="search-result-artist">${t.artist}</span>
            </div>
          </div>
        `).join('');
        dropdown.querySelectorAll('.search-result-item').forEach(item => {
          item.addEventListener('click', () => {
            const id = parseInt(item.dataset.id);
            const idx = TRACK_LIBRARY.findIndex(t => t.id === id);
            if (idx >= 0) loadTrack(idx, true);
            dropdown.style.display = 'none';
            input.value = '';
          });
        });
      }
      dropdown.style.display = 'block';
    });

    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = 'none';
      }
    });

    // Bottom search bar — also searches and loads
    const ytInput = $('ytSearchInput');
    if (ytInput) {
      ytInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const query = ytInput.value.trim().toLowerCase();
          if (query.length < 2) return;
          const result = TRACK_LIBRARY.find(t =>
            t.title.toLowerCase().includes(query) ||
            t.artist.toLowerCase().includes(query) ||
            t.album.toLowerCase().includes(query)
          );
          if (result) {
            const idx = TRACK_LIBRARY.findIndex(t => t.id === result.id);
            if (idx >= 0) loadTrack(idx, true);
          }
        }
      });
    }

    const lyricsInput = $('lyricsSearchInput');
    if (lyricsInput) {
      lyricsInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const query = lyricsInput.value.trim().toLowerCase();
          if (query.length < 2) return;
          // Simulated lyrics search — just find a random track
          const idx = Math.floor(Math.random() * TRACK_LIBRARY.length);
          loadTrack(idx, true);
        }
      });
    }
  }

  /* ---------------- VOICE SEARCH ---------------- */
  function bindVoiceSearch() {
    const btn = $('voiceSearchBtn');
    if (!btn) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      btn.addEventListener('click', () => {
        btn.classList.add('recording');
        setTimeout(() => {
          btn.classList.remove('recording');
          // Simulate voice result — pick random track
          const idx = Math.floor(Math.random() * TRACK_LIBRARY.length);
          loadTrack(idx, true);
        }, 2000);
      });
      return;
    }

    let recognition = null;
    btn.addEventListener('click', () => {
      if (btn.classList.contains('recording')) {
        recognition?.stop();
        btn.classList.remove('recording');
        return;
      }
      recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      btn.classList.add('recording');

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim().toLowerCase();
        const result = TRACK_LIBRARY.find(t =>
          t.title.toLowerCase().includes(transcript) ||
          t.artist.toLowerCase().includes(transcript)
        );
        if (result) {
          const idx = TRACK_LIBRARY.findIndex(t => t.id === result.id);
          if (idx >= 0) loadTrack(idx, true);
        }
      };

      recognition.onerror = () => {
        // Fallback — pick random
        const idx = Math.floor(Math.random() * TRACK_LIBRARY.length);
        loadTrack(idx, true);
      };

      recognition.onend = () => {
        btn.classList.remove('recording');
      };

      recognition.start();
    });
  }

  /* ---------------- SUB-SIDEBAR NAVIGATION ---------------- */
  function bindSubSidebar() {
    document.querySelectorAll('.subnav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.subnav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        const cat = item.dataset.cat;
        // Filter carousels based on category
        if (cat === 'trending') {
          filterCarousel('trendingScroll', TRACK_LIBRARY.slice(0, 6));
        } else if (cat === 'recent') {
          filterCarousel('recentScroll', [...TRACK_LIBRARY].slice(6, 12).reverse());
        } else if (cat === 'favorites') {
          const favs = TRACK_LIBRARY.filter(t => favorites.has(t.id));
          filterCarousel('trendingScroll', favs.length > 0 ? favs : TRACK_LIBRARY.slice(0, 6));
        } else {
          renderTrendingCarousel();
          renderRecentCarousel();
        }
      });
    });

    // Mobile subsidebar close
    $('subSidebarClose')?.addEventListener('click', () => {
      $('musicSubSidebar')?.classList.remove('mobile-open');
      $('mobileBackdrop')?.classList.remove('show');
    });
  }

  function filterCarousel(containerId, tracks) {
    const container = $(containerId);
    if (!container) return;
    container.innerHTML = '';
    tracks.forEach((track, i) => {
      container.appendChild(createTrackCard(track, i));
    });
  }

  /* ---------------- AUDIO VISUALIZER ---------------- */
  function startVisualizer() {
    const canvas = $('audioVisualizer');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    function resize() {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    const bars = 48;
    let phase = 0;

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = canvas.width / bars;
      const gap = 2;

      for (let i = 0; i < bars; i++) {
        let amplitude;
        if (isPlaying) {
          amplitude = Math.abs(Math.sin(phase + i * 0.3)) * 0.5 +
            Math.abs(Math.sin(phase * 1.7 + i * 0.15)) * 0.3 +
            Math.random() * 0.2;
        } else {
          amplitude = 0.05 + Math.sin(phase * 0.3 + i * 0.2) * 0.03;
        }
        const barHeight = amplitude * canvas.height * 0.85;
        const x = i * barWidth + gap / 2;
        const y = canvas.height - barHeight;

        const gradient = ctx.createLinearGradient(0, y, 0, canvas.height);
        gradient.addColorStop(0, 'rgba(0, 234, 255, 0.9)');
        gradient.addColorStop(0.5, 'rgba(0, 234, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(0, 234, 255, 0.1)');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth - gap, barHeight);
      }

      phase += 0.06;
      requestAnimationFrame(draw);
    }
    draw();
  }

  /* ---------------- CLOCK ---------------- */
  function startClock() {
    const clock = $('headerClock');
    if (!clock) return;
    function tick() {
      const now = new Date();
      const h = String(now.getUTCHours()).padStart(2, '0');
      const m = String(now.getUTCMinutes()).padStart(2, '0');
      const s = String(now.getUTCSeconds()).padStart(2, '0');
      clock.textContent = `${h}:${m}:${s} UTC`;
    }
    tick();
    setInterval(tick, 1000);
  }

  /* ---------------- KEYBOARD SHORTCUTS ---------------- */
  document.addEventListener('keydown', (e) => {
    // Ignore when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    if (e.code === 'Space') {
      e.preventDefault();
      togglePlay();
    } else if (e.code === 'ArrowRight' && e.shiftKey) {
      e.preventDefault();
      nextTrack();
    } else if (e.code === 'ArrowLeft' && e.shiftKey) {
      e.preventDefault();
      prevTrack();
    }
  });

})();

/* global CSRF_TOKEN */
(() => {
  const qs = (s, p=document) => p.querySelector(s);
  const qsa = (s, p=document) => [...p.querySelectorAll(s)];
  const POST = (url, data) => fetch(url, {
    method: "POST",
    headers: { "Content-Type":"application/json", "X-CSRFToken": CSRF_TOKEN },
    body: JSON.stringify(data||{})
  }).then(r => r.json());

  const COLORS = ["#fb7185", "#60a5fa"]; // Jugador A/B
  let BOARD = [];
  let WORDS = [];
  let FOUND = new Set();
  let PROGRESS = 0;
  let ACTIVE = {};   // selection_id -> {color, path:[[i,j],...]}
  let LOCKED = new Set(); // "i,j" string keys
  let BOARD_SIZE = 10;

  const elBoard = qs("#ws-board");
  const elWords = qs("#ws-words");
  const elProgress = qs("#ws-progress");
  const elComplete = qs("#complete-overlay");
  let isComplete = false;

  const key = (i,j) => `${i},${j}`;

  function paintBoard() {
    elBoard.style.gridTemplateColumns = `repeat(${BOARD_SIZE}, 42px)`;
    elBoard.innerHTML = "";
    for (let i=0;i<BOARD_SIZE;i++){
      for (let j=0;j<BOARD_SIZE;j++){
        const d = document.createElement("div");
        d.className = "ws-cell";
        d.dataset.i = i; d.dataset.j = j;
        d.textContent = (BOARD[i][j] || "").toString().toUpperCase();
        elBoard.appendChild(d);
      }
    }
  }

  function paintWords() {
    elWords.innerHTML = "";
    for (const w of WORDS) {
      const li = document.createElement("li");
      li.textContent = w;
      if (FOUND.has(w)) li.classList.add("found");
      elWords.appendChild(li);
    }
    elProgress.textContent = `Progreso: ${PROGRESS.toFixed(0)}%`;
  }

  function lockCellsFromActive() {
    qsa(".ws-cell").forEach(c => {
      const k = key(+c.dataset.i, +c.dataset.j);
      c.classList.toggle("locked", LOCKED.has(k));
    });
  }

  function colorActivePaths() {
    qsa(".ws-cell").forEach(c => c.style.outline = "");
    Object.values(ACTIVE).forEach(sel => {
      sel.path.forEach(([i,j]) => {
        const cell = qs(`.ws-cell[data-i="${i}"][data-j="${j}"]`);
        if (cell) cell.style.outline = `3px solid ${sel.color}`;
      });
    });
  }

  function markFound(word) {
    FOUND.add(word);
  }

  function showComplete() {
    isComplete = true;
    if (elComplete) {
      elComplete.classList.add("is-open");
      elComplete.setAttribute("aria-hidden", "false");
    }
  }

  // --- EVENTOS POINTER ---
  const pointerMap = new Map(); // pointerId -> {selection_id,color}

  async function pointerDown(e) {
    if (!(e.target.classList.contains("ws-cell"))) return;

    const i = +e.target.dataset.i;
    const j = +e.target.dataset.j;
    const k = key(i,j);
    if (LOCKED.has(k)) return;

    const color = (pointerMap.size === 0) ? COLORS[0] : COLORS[1];

    const resp = await POST("/etapasJuego/api/select/start/", { color, start:[i,j] });
    if (!resp.ok) return;
    const sid = resp.selection_id;

    pointerMap.set(e.pointerId, { selection_id: sid, color });
    ACTIVE = resp.active_selections || ACTIVE;
    LOCKED = new Set((resp.locked_cells || []).map(x => `${x[0]},${x[1]}`));
    lockCellsFromActive();
    colorActivePaths();

    e.target.setPointerCapture(e.pointerId);
  }

  async function pointerMove(e) {
    if (!pointerMap.has(e.pointerId)) return;
    const info = pointerMap.get(e.pointerId);
    const el = document.elementFromPoint(e.clientX, e.clientY);
    if (!el || !el.classList || !el.classList.contains("ws-cell")) return;

    const i = +el.dataset.i;
    const j = +el.dataset.j;
    const k = key(i,j);
    if (LOCKED.has(k)) return;

    const resp = await POST("/etapasJuego/api/select/extend/", {
      selection_id: info.selection_id, cell: [i,j]
    });
    if (!resp.ok) return;
    ACTIVE = resp.active_selections || ACTIVE;
    LOCKED = new Set((resp.locked_cells || []).map(x => `${x[0]},${x[1]}`));
    lockCellsFromActive();
    colorActivePaths();
  }

  async function pointerUp(e) {
    if (!pointerMap.has(e.pointerId)) return;
    const info = pointerMap.get(e.pointerId);
    pointerMap.delete(e.pointerId);

    const resp = await POST("/etapasJuego/api/select/commit/", {
      selection_id: info.selection_id
    });
    if (!resp.ok) return;

    if (resp.result === "found" && resp.word) {
      markFound(resp.word);
      if (window.TokenCounter) {
        window.TokenCounter.addOnce(`ws-word-${resp.word}`, 2);
      }
      paintWords();
      qsa(".ws-cell").forEach(c => {
        if (c.style.outline && c.style.outline.includes(info.color)) {
          c.classList.add("found");
          c.style.outline = "";
        }
      });
    } else if (resp.result === "already_found") {
      qsa(".ws-cell").forEach(c => {
        if (c.style.outline && c.style.outline.includes(info.color)) {
          c.animate([{ background:"#fde68a" }, { background:"#f3f4f6" }], { duration: 600 });
          c.style.outline = "";
        }
      });
    } else {
      qsa(".ws-cell").forEach(c => {
        if (c.style.outline && c.style.outline.includes(info.color)) {
          c.animate(
            [{ transform:"translateX(0px)" }, { transform:"translateX(6px)" }, { transform:"translateX(0px)"}],
            { duration: 150 }
          );
          c.style.outline = "";
        }
      });
    }

    ACTIVE = {};
    LOCKED = new Set();
    lockCellsFromActive();
    colorActivePaths();

    if (resp.found_words) {
      FOUND = new Set(resp.found_words);
    }
    if (typeof resp.progress_pct === "number") {
      PROGRESS = resp.progress_pct;
      elProgress.textContent = `Progreso: ${PROGRESS.toFixed(0)}%`;
    }
    if (resp.ended) {
      showComplete();
    }
  }

  function bindEvents() {
    elBoard.addEventListener("pointerdown", pointerDown);
    elBoard.addEventListener("pointermove", pointerMove);
    elBoard.addEventListener("pointerup", pointerUp);
    elBoard.addEventListener("pointercancel", pointerUp);
  }

  // === INIT con reset forzado para limpiar estado persistente ===
  async function init() {
    try {
      // Resetea la sesión actual en backend (ignora errores si no existe)
      await POST("/etapasJuego/api/reset/", {});
    } catch (e) {
      /* noop */
    }

    // Pide una sesión nueva limpia
    let resp = await POST("/etapasJuego/api/init/", {});

    // Por si acaso el backend devolviera algo ya 'found', normalizamos
    if (resp && resp.ended === true) {
      await POST("/etapasJuego/api/reset/", {});
      resp = await POST("/etapasJuego/api/init/", {});
    }

    BOARD = resp.soup || [];
    WORDS = resp.words || [];
    FOUND = new Set(resp.found_words || []); // debería venir vacío tras reset
    PROGRESS = resp.progress_pct || 0;
    BOARD_SIZE = resp.board_size || 10;

    if (elComplete) elComplete.hidden = true;

    paintBoard();
    paintWords();
    lockCellsFromActive();
    colorActivePaths();
  }

  // ===== Cronómetro simple 5:00 → 0:00 (solo display) =====
  function startSimpleTimer(durationSeconds = 300) {
    const elTimer = document.getElementById("ws-timer");
    if (!elTimer) return;
    const nextUrl = elTimer.dataset.nextUrl;

    let remaining = durationSeconds;
    let timeupShown = false;
    const format = (t) => {
      const m = Math.floor(t / 60);
      const s = t % 60;
      return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    };

    elTimer.textContent = format(remaining);

    const interval = setInterval(() => {
      remaining = Math.max(remaining - 1, 0);
      elTimer.textContent = format(remaining);
      if (remaining === 0) {
        clearInterval(interval);
        if (isComplete && nextUrl) {
          window.location.href = nextUrl;
          return;
        }
        if (!timeupShown && typeof window.showTimeupOverlay === "function") {
          timeupShown = true;
          window.showTimeupOverlay();
        }
      }
    }, 1000);
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bindEvents();
    await init();
    const timerEl = document.getElementById("ws-timer");
    const dur = parseInt(timerEl?.dataset.durationSeconds, 10);
    startSimpleTimer(Number.isFinite(dur) ? dur : 300); // 5 minutos por defecto
  });
})();

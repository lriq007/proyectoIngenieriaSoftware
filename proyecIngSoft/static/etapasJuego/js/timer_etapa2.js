document.addEventListener("DOMContentLoaded", () => {
  // ---------- Config ----------
  const VERSION       = "v2"; // súbelo si quieres forzar un reset global
  const STORAGE_KEY   = `E2_TIMER_END_AT_${VERSION}`;
  const DURATION_SEC  = 600; // 10:00

  // Puede haber timer en etapa2.html y/o etapa2_1.html
  const timers = Array.from(document.querySelectorAll("#e2-timer"));
  if (!timers.length) return;

  // Evita duplicar interval si el script se inyecta dos veces
  if (window.__E2_TIMER_ACTIVE__) return;
  window.__E2_TIMER_ACTIVE__ = true;

  // --------- Reglas de reseteo ----------
  // 1) Flag explícito desde la plantilla (solo en etapa2.html)
  const forceResetByFlag = !!window.E2_FORCE_RESET;

  // 2) Por URL: ?reset_timer=1
  const url = new URL(window.location.href);
  const forceResetByQuery = url.searchParams.get("reset_timer") === "1";

  // 3) Por ruta (robusto): contiene "/etapa2" y NO contiene "/etapa2_1"
  const p = url.pathname.replace(/\/+$/,""); // quita / final
  const forceResetByPath = /\/etapa2(?:$|\/)/.test(p) && !/\/etapa2_1(?:$|\/)/.test(p);

  if (forceResetByFlag || forceResetByQuery || forceResetByPath) {
    try { localStorage.removeItem(STORAGE_KEY); } catch(_) {}
  }

  // --------- Cargar/crear fin de timer ----------
  const now = Date.now();
  let endAt = Number(localStorage.getItem(STORAGE_KEY));

  // Si no hay fin guardado o ya expiró, crea uno nuevo
  if (!endAt || Number.isNaN(endAt) || endAt <= now) {
    endAt = now + DURATION_SEC * 1000;
    try { localStorage.setItem(STORAGE_KEY, String(endAt)); } catch(_) {}
  }

  const fmt = (t) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  let lastShown = null;

  function render() {
    const remainingMs  = Math.max(0, endAt - Date.now());
    const remainingSec = Math.floor(remainingMs / 1000);

    if (remainingSec !== lastShown) {
      const txt = fmt(remainingSec);
      timers.forEach(el => (el.textContent = txt));
      lastShown = remainingSec;
    }
    return remainingSec > 0;
  }

  // Primer pintado e intervalo
  render();
  const iv = setInterval(() => {
    if (!render()) {
      clearInterval(iv);
      // Descomenta si quieres que al llegar a 00:00, al recargar inicie otra vez:
      // try { localStorage.removeItem(STORAGE_KEY); } catch(_) {}
    }
  }, 250);

  // Sincroniza si otra pestaña/ventana cambia el valor
  window.addEventListener("storage", (e) => {
    if (e.key === STORAGE_KEY) {
      const val = Number(e.newValue);
      if (!Number.isNaN(val) && val > 0) {
        endAt = val;
        render();
      }
    }
  });
});

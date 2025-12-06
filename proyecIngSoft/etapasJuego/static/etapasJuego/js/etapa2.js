document.addEventListener("DOMContentLoaded", () => {
  const TIMER_KEY = "E2_TIMER_END_AT_v1"; // persistencia
  const timers = Array.from(document.querySelectorAll("#e2-timer"));
  if (!timers.length) return;

  const durationFromDom = parseInt(timers[0].dataset.durationSeconds, 10);
  const DURATION_SEC = Number.isFinite(durationFromDom) ? durationFromDom : 600; // 10 minutos por defecto

  // Puede haber timer en etapa2.html o en etapa2_1.html (o en ambas)
  // Evita crear múltiples intervals si se reinyecta el script
  if (window.__E2_TIMER_ACTIVE__) return;
  window.__E2_TIMER_ACTIVE__ = true;

  const now = Date.now();
  let endAt = Number(localStorage.getItem(TIMER_KEY));

  // Si no hay fin guardado o ya expiró, crea uno nuevo
  if (!endAt || Number.isNaN(endAt) || endAt <= now) {
    endAt = now + DURATION_SEC * 1000;
    localStorage.setItem(TIMER_KEY, String(endAt));
  }

  const fmt = (t) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  let lastShown = null;
  let timeupShown = false;

  function render() {
    const remainingMs = Math.max(0, endAt - Date.now());
    const remainingSec = Math.floor(remainingMs / 1000);

    // solo repintamos si cambió el segundo
    if (remainingSec !== lastShown) {
      const txt = fmt(remainingSec);
      timers.forEach(el => (el.textContent = txt));
      lastShown = remainingSec;
    }

    if (remainingSec <= 0) {
      if (!timeupShown && typeof window.showTimeupOverlay === "function") {
        timeupShown = true;
        window.showTimeupOverlay();
      }
      return false;
    }
    return true;
  }

  // Primer pintado inmediato
  render();

  // Intervalo estable (250ms para suavidad; solo repinta si cambia el segundo)
  const iv = setInterval(() => {
    if (!render()) {
      clearInterval(iv);
      // Si quisieras que al terminar vuelva a iniciar en 10:00 cuando recargues, descomenta:
      // localStorage.removeItem(TIMER_KEY);
    }
  }, 250);

  // Sincroniza si otra pestaña cambia el storage
  window.addEventListener("storage", (e) => {
    if (e.key === TIMER_KEY) {
      const val = Number(e.newValue);
      if (!Number.isNaN(val) && val > 0) {
        endAt = val;
        render();
      }
    }
  });
});

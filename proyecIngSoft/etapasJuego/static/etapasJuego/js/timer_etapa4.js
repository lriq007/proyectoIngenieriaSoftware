(() => {
  // Evita dobles cargas
  if (window.__E4_TIMER_ACTIVE__) return;
  window.__E4_TIMER_ACTIVE__ = true;

  const TOTAL_SECONDS = 10 * 60; // 10:00

  const pad2 = (n) => String(n).padStart(2, "0");
  const fmt = (sec) => `${pad2(Math.floor(sec / 60))}:${pad2(sec % 60)}`;

  function startTimer() {
    const el = document.getElementById("e4-timer");
    if (!el) return;

    const endAt = Date.now() + TOTAL_SECONDS * 1000;

    el.textContent = fmt(TOTAL_SECONDS);

    const alignAndStart = () => {
      const tick = () => {
        const remaining = Math.max(0, Math.ceil((endAt - Date.now()) / 1000));
        el.textContent = fmt(remaining);
        if (remaining === 0) clearInterval(iv);
      };
      tick();
      iv = setInterval(tick, 1000);
    };

    const msToNextSecond = 1000 - (Date.now() % 1000);
    let iv = null;
    setTimeout(alignAndStart, msToNextSecond);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startTimer, { once: true });
  } else {
    startTimer();
  }

  // Para pruebas desde consola:
  window.startE4Timer = startTimer;
})();

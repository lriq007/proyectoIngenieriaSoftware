(() => {
  const fmt = (t) => {
    const m = Math.floor(t / 60);
    const s = t % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  function openTimeupOverlay() {
    if (typeof window.showTimeupOverlay === "function") {
      window.showTimeupOverlay();
      return;
    }
    const overlay = document.getElementById("timeup-overlay");
    if (!overlay) return;
    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
  }

  function startTimer() {
    const el = document.getElementById("rompehielo-timer");
    if (!el) return;

    const durationAttr = parseInt(el.dataset.durationSeconds, 10);
    let remaining = Number.isFinite(durationAttr) ? durationAttr : 300;

    el.textContent = fmt(remaining);
    const iv = setInterval(() => {
      remaining -= 1;
      if (remaining > 0) {
        el.textContent = fmt(remaining);
        return;
      }
      el.textContent = "00:00";
      clearInterval(iv);
      openTimeupOverlay();
    }, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startTimer, { once: true });
  } else {
    startTimer();
  }
})();

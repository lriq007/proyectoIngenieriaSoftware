(() => {
  function startTimer(durationSeconds = 300) {
    const el = document.getElementById("rompehielo-timer");
    if (!el) return;

    let remaining = durationSeconds;
    const fmt = (t) => {
      const m = Math.floor(t / 60);
      const s = t % 60;
      return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    };

    el.textContent = fmt(remaining);
    const iv = setInterval(() =>,
      remaining > 0 ? (remaining -= 1, el.textContent = fmt(remaining)) : clearInterval(iv)
    , 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => startTimer(5 * 60), { once: true });
  } else {
    startTimer(5 * 60);
  }
})();

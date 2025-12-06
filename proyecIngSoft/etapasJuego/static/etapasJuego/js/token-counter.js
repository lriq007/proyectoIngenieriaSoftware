(() => {
  const STORAGE_TOTAL = "token_counter_total_v1";
  const STORAGE_EVENTS = "token_counter_events_v1";

  const qs = (s, p = document) => p.querySelector(s);

  const loadTotal = () => {
    const val = Number(localStorage.getItem(STORAGE_TOTAL));
    return Number.isFinite(val) ? val : 0;
  };
  const saveTotal = (val) => localStorage.setItem(STORAGE_TOTAL, String(val));

  const loadEvents = () => {
    try {
      const raw = localStorage.getItem(STORAGE_EVENTS);
      if (!raw) return new Set();
      return new Set(JSON.parse(raw));
    } catch (e) {
      return new Set();
    }
  };
  const saveEvents = (events) => {
    localStorage.setItem(STORAGE_EVENTS, JSON.stringify([...events]));
  };

  let eventsSet = loadEvents();
  let total = loadTotal();
  let elCounter = null;
  let elValue = null;

  function ensureCounter() {
    if (elCounter) return;
    elCounter = document.createElement("div");
    elCounter.id = "token-counter";
    elCounter.className = "token-counter";
    elCounter.innerHTML = `
      <span class="token-counter-label">Tokens</span>
      <span class="token-counter-value" id="token-counter-value">0</span>
    `;
    document.body.appendChild(elCounter);
    elValue = qs("#token-counter-value");
  }

  function render() {
    if (!elValue) return;
    elValue.textContent = total;
  }

  function flash() {
    if (!elCounter) return;
    elCounter.classList.add("flash");
    clearTimeout(elCounter._t);
    elCounter._t = setTimeout(() => elCounter.classList.remove("flash"), 900);
  }

  function add(amount = 0) {
    const delta = Number(amount) || 0;
    if (!delta) return total;
    total = Math.max(0, Math.round(total + delta));
    saveTotal(total);
    render();
    flash();
    return total;
  }

  function addOnce(key, amount = 0) {
    if (!key) return total;
    if (eventsSet.has(key)) return total;
    eventsSet.add(key);
    saveEvents(eventsSet);
    return add(amount);
  }

  function set(value = 0) {
    total = Math.max(0, Math.round(Number(value) || 0));
    saveTotal(total);
    render();
    return total;
  }

  document.addEventListener("DOMContentLoaded", () => {
    ensureCounter();
    total = loadTotal();
    render();
  });

  window.TokenCounter = {
    add,
    addOnce,
    set,
    get: () => total,
  };
})();

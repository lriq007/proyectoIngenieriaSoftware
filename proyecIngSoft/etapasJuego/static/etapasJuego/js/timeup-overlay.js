(() => {
  window.showTimeupOverlay = function showTimeupOverlay() {
    const overlay = document.getElementById("timeup-overlay");
    if (!overlay) return;
    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
  };
})();

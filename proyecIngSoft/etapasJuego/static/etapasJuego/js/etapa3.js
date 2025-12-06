(() => {
  const input = document.getElementById("legoInput");
  const btn   = document.getElementById("legoBtn");
  const img   = document.getElementById("legoImg");
  const clear = document.getElementById("legoClear");

  // Verificación más flexible para el clear button
  if (!input || !btn || !img) {
    console.error('Elementos esenciales del lego uploader no encontrados');
    return;
  }

  const MAX_SIZE = 8 * 1024 * 1024; // 8 MB
  let objectUrl = null;

  function showError(msg) {
    alert(msg);
  }

  function resetPreview() {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    img.src = "";
    img.hidden = true;
    if (clear) clear.hidden = true;
    btn.classList.remove("has-image");
  }

  function showPreview(file) {
    if (!file) return;

    if (!file.type || !file.type.startsWith("image/")) {
      showError("El archivo debe ser una imagen (JPG o PNG).");
      return;
    }
    if (file.size > MAX_SIZE) {
      showError("La imagen supera el límite de 8 MB.");
      return;
    }

    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    img.src = objectUrl;
    img.hidden = false;
    if (clear) clear.hidden = false;
    btn.classList.add("has-image");
    
    if (window.TokenCounter) {
      window.TokenCounter.addOnce("lego-upload", 6);
    }
    
    console.log('Imagen cargada correctamente:', file.name);
  }

  // Input clásico
  input.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    showPreview(file);
  });

  // Teclado accesible en el label
  btn.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      input.click();
    }
  });

  // Click directo en el botón (para mejor UX)
  btn.addEventListener("click", (e) => {
    // Solo activar el input si no hay imagen
    if (!btn.classList.contains("has-image")) {
      input.click();
    }
  });

  // Drag & Drop en el botón grande
  ["dragenter","dragover"].forEach(ev => {
    btn.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      btn.classList.add("is-dragover");
      btn.style.borderColor = '#FF5FA2';
      btn.style.transform = 'translateY(-2px)';
    });
  });
  
  ["dragleave","dragend","drop"].forEach(ev => {
    btn.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      btn.classList.remove("is-dragover");
      btn.style.borderColor = '#FFD24A';
      btn.style.transform = 'translateY(0)';
    });
  });
  
  btn.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (!file) return;
    showPreview(file);
  });

  // Botón limpiar (si existe)
  if (clear) {
    clear.addEventListener("click", () => {
      input.value = "";
      resetPreview();
    });
  }

  // Estado inicial
  resetPreview();
})();

// Timer function - mantenla igual
document.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("e3-timer");
  if (!el) return;

  const dur = parseInt(el.dataset.durationSeconds, 10);
  const DURATION = Number.isFinite(dur) ? dur : 15 * 60; // 15 minutos en segundos
  let remaining = DURATION;
  let timeupShown = false;

  function fmt(sec){
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  }

  // pintar inicial
  el.textContent = fmt(remaining);

  // intervalo simple; no persiste entre recargas
  const iv = setInterval(() => {
    remaining = Math.max(0, remaining - 1);
    el.textContent = fmt(remaining);
    if (remaining <= 0) {
      clearInterval(iv);
      if (!timeupShown && typeof window.showTimeupOverlay === "function") {
        timeupShown = true;
        window.showTimeupOverlay();
      }
    }
  }, 1000);
});

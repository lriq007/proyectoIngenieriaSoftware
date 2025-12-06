document.addEventListener("DOMContentLoaded", () => {
    const elements = document.querySelectorAll(".typewriter");

    elements.forEach((el, index) => {
        const text = el.dataset.text;
        el.textContent = "";  // Start empty

        let i = 0;
        const speed = 25; // ms por carácter

        function typeLetter() {
            if (i < text.length) {
                el.textContent += text.charAt(i);
                i++;
                setTimeout(typeLetter, speed);
            }
        }

        // Pequeño delay entre tarjetas (como chat gpt)
        setTimeout(typeLetter, index * 300);
    });
});

// Timer de etapa 4: mismo patrón que otras etapas
document.addEventListener("DOMContentLoaded", () => {
  const el = document.getElementById("e4-timer");
  if (!el) return;

  const dur = parseInt(el.dataset.durationSeconds, 10);
  const DURATION = Number.isFinite(dur) ? dur : 10 * 60; // fallback 10 min
  let remaining = DURATION;
  let timeupShown = false;

  const fmt = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  };

  // pintar inicial
  el.textContent = fmt(remaining);

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

// Guardar pitch (mismo patrón que Bubble Map)
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btnGuardarPitch");
  const textarea = document.getElementById("pitchText");
  const feedback = document.getElementById("pitchFeedback");
  if (!btn || !textarea) return;

  const saveUrl = btn.dataset.saveUrl;
  const redirectUrl = btn.dataset.redirectUrl;

  const getCsrfToken = () => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  };

  const showMessage = (msg, type = "info") => {
    if (!feedback) return;
    feedback.textContent = msg;
    feedback.classList.remove("error", "success");
    if (type === "error") feedback.classList.add("error");
    if (type === "success") feedback.classList.add("success");
  };

  btn.addEventListener("click", async () => {
    const pitch = (textarea.value || "").trim();
    if (!pitch) {
      showMessage("Escribe tu pitch antes de guardar.", "error");
      return;
    }

    btn.disabled = true;
    showMessage("Guardando...");
    try {
      const res = await fetch(saveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ pitch_text: pitch }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        showMessage("No se pudo guardar el pitch. Inténtalo nuevamente.", "error");
      } else {
        showMessage("Pitch guardado con éxito.", "success");
        if (window.TokenCounter) {
          window.TokenCounter.addOnce("pitch-guardado", 8);
        }
        if (redirectUrl) {
          window.location.href = redirectUrl;
        }
      }
    } catch (error) {
      console.error(error);
      showMessage("Ocurrió un error al guardar.", "error");
    } finally {
      btn.disabled = false;
    }
  });
});

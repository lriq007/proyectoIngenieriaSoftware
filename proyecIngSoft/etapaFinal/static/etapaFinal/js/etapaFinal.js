(() => {
  const qs = (s, p = document) => p.querySelector(s);
  const qsa = (s, p = document) => [...p.querySelectorAll(s)];

  function getCsrfToken() {
    const name = "csrftoken";
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    for (const c of cookies) {
      if (c.startsWith(name + "=")) {
        return decodeURIComponent(c.split("=").slice(1).join("="));
      }
    }
    const input = qs("input[name='csrfmiddlewaretoken']");
    return input ? input.value : "";
  }

  function flashStatus(msg, isError = false) {
    const el = qs("#ef-status");
    if (!el) return;
    el.textContent = msg;
    el.style.opacity = "1";
    el.style.color = isError ? "#c62828" : "";
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = "0.0"; }, 2000);
  }

  function collectEvaluations() {
    const cards = qsa(".ef-eval-card[data-equipo-id]");
    const evaluaciones = [];

    cards.forEach(card => {
      const teamId = card.dataset.equipoId;
      const scores = {};
      const selects = qsa(".ef-score", card);
      selects.forEach(sel => {
        const field = sel.dataset.field;
        const val = sel.value ? parseInt(sel.value, 10) : null;
        scores[field] = Number.isInteger(val) ? val : null;
      });
      const comentario = qs(".ef-comment", card)?.value?.trim() || "";

      // Solo incluir si todos los puntajes están presentes
      const requiredFields = ["puntaje_equipo", "puntaje_empatia", "puntaje_creatividad", "puntaje_comunicacion"];
      const missing = requiredFields.some(f => !scores[f]);
      if (missing) return;

      evaluaciones.push({
        evaluado_id: parseInt(teamId, 10),
        ...scores,
        comentario,
      });
    });

    return evaluaciones;
  }

  function sumTokenEstimate() {
    const cards = qsa(".ef-eval-card[data-equipo-id]");
    let total = 0;
    cards.forEach(card => {
      const inputs = qsa(".ef-score", card);
      inputs.forEach(inp => {
        const val = inp.value ? parseInt(inp.value, 10) : 0;
        if (Number.isInteger(val)) total += val;
      });
    });
    return total;
  }

  function bindTokenCounter() {
    const counter = qs("#ef-token-counter");
    const valueEl = qs("#ef-token-value");
    if (!counter || !valueEl) return;

    let lastTotal = 0;
    const animate = () => {
      counter.classList.add("flash");
      clearTimeout(counter._t);
      counter._t = setTimeout(() => counter.classList.remove("flash"), 800);
    };

    const recalc = () => {
      const total = sumTokenEstimate();
      valueEl.textContent = total;
      if (total > lastTotal) {
        animate();
      }
      lastTotal = total;
    };

    document.addEventListener("input", (e) => {
      if (e.target && e.target.classList.contains("ef-score")) {
        recalc();
      }
    });

    recalc();
  }

  async function submitEvaluations() {
    const form = qs("#ef-form");
    const saveUrl = form?.dataset.saveUrl;
    if (!form || !saveUrl) return;

    const evaluaciones = collectEvaluations();
    if (!evaluaciones.length) {
      flashStatus("Completa todos los puntajes antes de enviar", true);
      return;
    }

    const payload = { evaluaciones };
    try {
      const resp = await fetch(saveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      const ok = data && (data.ok === true || data.status === "ok");
      if (!resp.ok || !ok) {
        throw new Error((data && data.msg) || "Error al guardar");
      }
      flashStatus((data && data.msg) || "Coevaluaciones enviadas correctamente");
    } catch (err) {
      flashStatus(err.message || "No se pudo enviar", true);
    }
  }

  function updatePhotoPreview(fotoUrl) {
    let preview = qs("#ef-photo-preview");
    if (!preview) return;

    const hasUrl = Boolean(fotoUrl);
    if (hasUrl) {
      if (preview.tagName !== "IMG") {
        const img = document.createElement("img");
        img.id = "ef-photo-preview";
        img.className = "photo-preview";
        img.alt = "Foto del equipo seleccionado";
        preview.replaceWith(img);
        preview = img;
      }
      preview.src = fotoUrl;
    } else {
      if (preview.tagName === "IMG") {
        const placeholder = document.createElement("div");
        placeholder.id = "ef-photo-preview";
        placeholder.className = "photo-placeholder";
        placeholder.textContent = "Sin foto aún";
        preview.replaceWith(placeholder);
        preview = placeholder;
      } else {
        preview.textContent = "Sin foto aún";
      }
    }
  }

  function setActiveTeam(teamId) {
    const buttons = qsa(".ef-team-btn");
    const cards = qsa(".ef-eval-card[data-equipo-id]");
    let fotoUrl = "";

    buttons.forEach(btn => {
      const isActive = btn.dataset.equipoId === teamId;
      btn.classList.toggle("is-active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
      if (isActive && btn.dataset.fotoUrl) {
        fotoUrl = btn.dataset.fotoUrl;
      }
    });

    cards.forEach(card => {
      const isActive = card.dataset.equipoId === teamId;
      card.classList.toggle("is-hidden", !isActive);
      if (isActive && !fotoUrl && card.dataset.fotoUrl) {
        fotoUrl = card.dataset.fotoUrl;
      }
    });

    updatePhotoPreview(fotoUrl);
  }

  function bindTeamSelection() {
    const buttons = qsa(".ef-team-btn");
    if (!buttons.length) return;

    buttons.forEach(btn => {
      btn.addEventListener("click", () => setActiveTeam(btn.dataset.equipoId));
    });

    const initial = buttons.find(b => b.classList.contains("is-active")) || buttons[0];
    if (initial) {
      setActiveTeam(initial.dataset.equipoId);
    }
  }

  function bind() {
    const btnSubmit = qs("#ef-submit");
    if (btnSubmit) {
      btnSubmit.addEventListener("click", submitEvaluations);
    }
    bindTeamSelection();
    bindTokenCounter();
  }

  function init() {
    bind();
  }

  document.addEventListener("DOMContentLoaded", init);
})();

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
    const cards = qsa(".ef-card[data-equipo-id]");
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

  function bind() {
    const btnSubmit = qs("#ef-submit");
    if (btnSubmit) {
      btnSubmit.addEventListener("click", submitEvaluations);
    }
  }

  function init() {
    bind();
  }

  document.addEventListener("DOMContentLoaded", init);
})();

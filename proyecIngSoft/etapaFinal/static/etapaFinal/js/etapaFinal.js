(() => {
  // === Configuración ===
  const GROUPS = ["Grupo A", "Grupo B", "Grupo C", "Grupo D"];

// Plantilla de preguntas (mismas para todos los grupos)
const QUESTIONS = [
  {
    id: "equipo",
    text: "¿El equipo mostró buena coordinación y participación equilibrada durante la presentación?"
  },
  {
    id: "empatia",
    text: "¿El equipo demostró comprensión y sensibilidad hacia las necesidades del usuario o problema abordado?"
  },
  {
    id: "creatividad",
    text: "¿La propuesta y su presentación reflejaron originalidad e innovación?"
  },
  {
    id: "comunicacion",
    text: "¿La presentación fue clara, atractiva y mantuvo la atención del público?"
  },
  {
    id: "evaluacion_general",
    text: "¿Qué tan efectiva consideras la presentación del grupo en su conjunto?"
  }
];


  // Estado: puntajes por grupo y pregunta (1..5)
  const state = {
    currentGroup: GROUPS[0],
    scores: {} // { "Grupo A": { claridad: 4, contenido: 3, ... }, ... }
  };

  // Si quieres impedir evaluar tu propio grupo, define window.CURRENT_TEAM en la plantilla
  const myTeam = window.CURRENT_TEAM || null;

  // === Helpers ===
  const qs = (s, p = document) => p.querySelector(s);
  const qsa = (s, p = document) => [...p.querySelectorAll(s)];

  function ensureGroupState(group) {
    if (!state.scores[group]) {
      state.scores[group] = {};
      QUESTIONS.forEach(q => { state.scores[group][q.id] = null; });
    }
  }

  function setCurrentGroup(group) {
    state.currentGroup = group;
    ensureGroupState(group);
    renderTabs();
    renderQuestions();
    flashStatus(`Editando evaluación de ${group}`);
  }

  function setScore(group, questionId, value) {
    ensureGroupState(group);
    state.scores[group][questionId] = value;
    renderQuestions(); // re-pinta para marcar el activo
  }

  function flashStatus(msg) {
    const el = qs("#ef-status");
    if (!el) return;
    el.textContent = msg;
    el.style.opacity = "1";
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = "0.0"; }, 1600);
  }

  // === Render: Tabs ===
  function renderTabs() {
    qsa(".ef-tab").forEach(btn => {
      const g = btn.dataset.group;
      const isActive = (g === state.currentGroup);
      btn.classList.toggle("ef-tab-active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");

      // Bloquear mi propio grupo (si aplica)
      if (myTeam && g === myTeam) {
        btn.disabled = true;
        btn.title = "No puedes evaluar tu propio grupo";
      } else {
        btn.disabled = false;
        btn.title = "";
      }
    });
  }

  // === Render: Preguntas + escala 1..5 ===
  function renderQuestions() {
    const root = qs("#ef-questions");
    root.innerHTML = "";

    const group = state.currentGroup;
    ensureGroupState(group);

    QUESTIONS.forEach(q => {
      const card = document.createElement("div");
      card.className = "ef-card";
      card.innerHTML = `
        <h2>${q.text} <small style="opacity:.7;font-weight:600">( ${group} )</small></h2>
        <div class="ef-scale" role="group" aria-label="Escala de evaluación 1 a 5">
        </div>
      `;

      const scale = card.querySelector(".ef-scale");
      for (let v = 1; v <= 5; v++) {
        const pill = document.createElement("button");
        pill.className = "ef-pill";
        pill.type = "button";
        pill.textContent = String(v);
        pill.setAttribute("aria-pressed", state.scores[group][q.id] === v ? "true" : "false");
        if (state.scores[group][q.id] === v) pill.classList.add("ef-pill-active");

        pill.addEventListener("click", () => {
          setScore(group, q.id, v);
          flashStatus(`(${group}) "${q.id}" = ${v}`);
        });

        scale.appendChild(pill);
      }

      root.appendChild(card);
    });
  }

  // === Limpia respuestas del grupo actual ===
  function clearCurrentGroup() {
    const g = state.currentGroup;
    QUESTIONS.forEach(q => { state.scores[g][q.id] = null; });
    renderQuestions();
    flashStatus(`Respuestas de ${g} limpiadas`);
  }

  // === Bind eventos de UI ===
  function bind() {
    // Click en tabs (delegado)
    const tabs = qsa(".ef-tab");
    tabs.forEach(btn => {
      btn.addEventListener("click", () => {
        const g = btn.dataset.group;
        if (btn.disabled) return; // no permitir si es mi propio grupo
        setCurrentGroup(g);
      });
    });

    // Botón limpiar
    const btnClear = qs("#ef-clear-group");
    if (btnClear) btnClear.addEventListener("click", clearCurrentGroup);
  }

  // === Init ===
  function init() {
    // Estado inicial
    GROUPS.forEach(g => ensureGroupState(g));
    // Si mi grupo está definido, evita arrancar en esa pestaña
    if (myTeam && state.currentGroup === myTeam) {
      const firstOther = GROUPS.find(g => g !== myTeam) || GROUPS[0];
      state.currentGroup = firstOther;
    }
    renderTabs();
    renderQuestions();
    bind();
  }

  document.addEventListener("DOMContentLoaded", init);
})();

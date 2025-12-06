(() => {
  const map = document.getElementById('bubbleMap');
  if (!map) return;

  const bubbles = Array.from(map.querySelectorAll('.bubble-question'));
  const saveBtn = document.getElementById('btnSaveBubble');
  const feedback = document.getElementById('bubbleFeedback');
  const payload = window.bubblePayload || {};

  const getCsrfToken = () => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  let currentActive = null;

  const setActive = (bubble) => {
    if (currentActive === bubble) return;
    if (currentActive) currentActive.classList.remove('is-active');
    currentActive = bubble;
    if (currentActive) currentActive.classList.add('is-active');
  };

  const handleBubbleClick = (bubble) => {
    if (currentActive === bubble) {
      bubble.classList.remove('is-active');
      currentActive = null;
      return;
    }
    setActive(bubble);
    const textarea = bubble.querySelector('textarea');
    if (textarea) {
      textarea.focus();
      textarea.select();
    }
  };

  const toggleHasContent = (bubble) => {
    const textarea = bubble.querySelector('textarea');
    if (!textarea) return;
    if (textarea.value.trim()) {
      bubble.classList.add('has-content');
    } else {
      bubble.classList.remove('has-content');
    }
  };

  const updateCharCount = (textarea) => {
    const charCount = textarea.nextElementSibling;
    if (!charCount) return;
    const current = textarea.value.length;
    const max = textarea.maxLength || 300;
    charCount.textContent = `${current} / ${max}`;
  };

  bubbles.forEach((bubble) => {
    bubble.addEventListener('click', () => handleBubbleClick(bubble));
    bubble.addEventListener('keydown', (evt) => {
      if (evt.key === 'Enter' || evt.key === ' ') {
        evt.preventDefault();
        handleBubbleClick(bubble);
      }
    });
    const textarea = bubble.querySelector('textarea');
    if (textarea) {
      textarea.addEventListener('input', () => {
        toggleHasContent(bubble);
        updateCharCount(textarea);
      });
      textarea.addEventListener('keydown', (e) => e.stopPropagation());
      textarea.addEventListener('click', (e) => e.stopPropagation());
      textarea.addEventListener('keyup', (e) => e.stopPropagation());
      toggleHasContent(bubble);
      updateCharCount(textarea);
    }
  });

  const collectResponses = () => {
    const answers = {};
    bubbles.forEach((bubble) => {
      const textarea = bubble.querySelector('textarea');
      if (!textarea) return;
      answers[bubble.dataset.key] = textarea.value.trim();
    });
    return answers;
  };

  const showMessage = (msg, type = 'info') => {
    if (!feedback) return;
    feedback.textContent = msg;
    feedback.classList.remove('error', 'success');
    if (type === 'error') feedback.classList.add('error');
    if (type === 'success') feedback.classList.add('success');
  };

  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const respuestas = collectResponses();
      saveBtn.disabled = true;
      showMessage('Guardando...');
      try {
        const res = await fetch(payload.saveUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          body: JSON.stringify({
            desafio_numero: payload.numero,
            respuestas,
          }),
        });
        const data = await res.json();
        if (!res.ok || !data.ok) {
          showMessage('No se pudo guardar. Inténtalo nuevamente.', 'error');
        } else {
          showMessage('Respuestas guardadas correctamente.', 'success');
          if (window.TokenCounter) {
            window.TokenCounter.addOnce('bubble-save', 6);
          }
        }
      } catch (error) {
        console.error(error);
        showMessage('Ocurrió un error al guardar.', 'error');
      } finally {
        saveBtn.disabled = false;
      }
    });
  }
})();

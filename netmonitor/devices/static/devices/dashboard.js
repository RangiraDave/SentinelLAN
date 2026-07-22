(() => {
  let modalTrigger = null;

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('is-open');
    document.body.classList.remove('modal-open');
    modalTrigger?.focus();
  }

  document.querySelectorAll('[data-modal-target]').forEach((button) => {
    button.addEventListener('click', () => {
      const modal = document.getElementById(button.dataset.modalTarget);
      if (!modal) return;
      modalTrigger = button;
      modal.classList.add('is-open');
      document.body.classList.add('modal-open');
      modal.querySelector('.popup-close, a, button')?.focus();
    });
  });

  document.querySelectorAll('.popup-overlay').forEach((modal) => {
    modal.addEventListener('click', (event) => {
      if (event.target === modal) closeModal(modal);
    });
    modal.querySelector('.popup-close')?.addEventListener('click', () => closeModal(modal));
  });

  document.addEventListener('keydown', (event) => {
    const modal = document.querySelector('.popup-overlay.is-open');
    if (event.key === 'Escape') closeModal(modal);
    if (event.key !== 'Tab' || !modal) return;
    const focusable = [...modal.querySelectorAll('a[href], button:not([disabled]), input, select, textarea')];
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  document.querySelectorAll('.scan-form').forEach((form) => {
    form.addEventListener('submit', () => {
      document.querySelectorAll('.scan-form button').forEach((button) => {
        button.disabled = true;
        const label = button.querySelector('.button-label');
        if (label) label.textContent = 'Scanning…';
      });
    });
  });

  if (document.body.dataset.autoScan === 'true') {
    const interval = Number(document.body.dataset.interval) * 1000;
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (interval > 0 && token) {
      window.setInterval(async () => {
        if (document.hidden || document.querySelector('.popup-overlay.is-open')) return;
        const response = await fetch(document.body.dataset.scanUrl, {
          method: 'POST',
          headers: {'X-CSRFToken': token, 'X-Requested-With': 'XMLHttpRequest'},
        });
        if (response.ok) window.location.reload();
      }, interval);
    }
  }
})();

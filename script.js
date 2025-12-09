const modalTriggers = document.querySelectorAll('[data-modal-target]');
const modals = document.querySelectorAll('.modal');
const body = document.body;

const openModal = (selector) => {
  const modal = document.querySelector(selector);
  if (!modal) return;

  modal.classList.add('modal--visible');
  modal.setAttribute('aria-hidden', 'false');
  modal.setAttribute('aria-modal', 'true');
  body.style.overflow = 'hidden';
};

const closeModal = (modal) => {
  modal.classList.remove('modal--visible');
  modal.setAttribute('aria-hidden', 'true');
  modal.setAttribute('aria-modal', 'false');
  if (![...modals].some((m) => m.classList.contains('modal--visible'))) {
    body.style.overflow = '';
  }
};

modalTriggers.forEach((trigger) => {
  trigger.addEventListener('click', () => {
    const target = trigger.getAttribute('data-modal-target');
    openModal(target);
  });
});

modals.forEach((modal) => {
  modal.addEventListener('click', (event) => {
    if (event.target.hasAttribute('data-modal-close')) {
      closeModal(modal);
    }
  });
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    modals.forEach((modal) => {
      if (modal.classList.contains('modal--visible')) {
        closeModal(modal);
      }
    });
  }
});

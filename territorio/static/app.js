// Browser interactions only. All records and business rules live in Python.
(() => {
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.querySelector('[data-close-menu]');
  const closeMenu = () => { sidebar.classList.remove('visible'); backdrop.hidden = true; };
  document.querySelector('[data-menu]')?.addEventListener('click', () => { sidebar.classList.add('visible'); backdrop.hidden = false; });
  backdrop?.addEventListener('click', closeMenu);
  document.querySelectorAll('[data-dialog]').forEach(button => button.addEventListener('click', () => document.getElementById(button.dataset.dialog).showModal()));
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => dialog.close()));
    dialog.addEventListener('click', e => { const r = dialog.getBoundingClientRect(); if (e.target === dialog && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) dialog.close(); });
  });
  document.querySelectorAll('form[method="post"]').forEach(form => form.addEventListener('submit', () => { form.querySelectorAll('button[type="submit"], .form-actions button:not([type="button"])').forEach(button => { button.disabled = true; }); }));
  const notice = document.getElementById('notice');
  let timer;
  window.notify = (message, error = false) => { clearTimeout(timer); notice.hidden = false; notice.classList.toggle('error', error); notice.setAttribute('role', error ? 'alert' : 'status'); notice.querySelector('span').textContent = message; timer = setTimeout(() => notice.hidden = true, 7000); };
  notice.querySelector('button').addEventListener('click', () => notice.hidden = true);
})();

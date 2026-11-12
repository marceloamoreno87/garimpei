(() => {
  document.querySelectorAll('[data-condition-form]').forEach(form => {
    form.addEventListener('submit', () => {
      form.setAttribute('aria-busy', 'true');
      form.querySelector('button[type=submit]').disabled = true;
      form.querySelector('.condition-pending').hidden = false;
    });
  });
  if (sessionStorage.getItem('condition-tab-focus')) {
    sessionStorage.removeItem('condition-tab-focus');
    document.querySelector('.condition-tabs [aria-selected=true]')?.focus();
  }
})();

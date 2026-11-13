(() => {
  if (window.garimpeiFormsLoaded) return;
  window.garimpeiFormsLoaded = true;
  function focusFeedback() {
    const summary = document.querySelector('#form-error, #identity-error');
    if (summary) {
      summary.focus();
    } else if (document.querySelector('[data-preview]')) {
      document.getElementById('new_product')?.focus();
    }
  }
  document.addEventListener('htmx:beforeSwap', event => {
    if (!event.detail.requestConfig?.elt?.matches('form[hx-boost]')) return;
    if ([403, 409, 422, 500, 503].includes(event.detail.xhr.status)) {
      event.detail.shouldSwap = true;
      event.detail.isError = false;
    }
  });
  document.addEventListener('htmx:afterSettle', focusFeedback);
  document.addEventListener('DOMContentLoaded', focusFeedback);
  document.addEventListener('htmx:beforeRequest', event => {
    if (event.detail.elt.matches('form')) event.detail.elt.setAttribute('aria-busy', 'true');
  });
  document.addEventListener('htmx:afterRequest', event => {
    if (event.detail.elt.matches('form')) event.detail.elt.removeAttribute('aria-busy');
  });
  const transportFailure = event => {
    const form = event.detail.elt?.closest('form[hx-boost]');
    if (!form) return;
    form.querySelector('#transport-error')?.remove();
    const message = document.createElement('p');
    form.removeAttribute('aria-busy');
    message.id = 'transport-error';
    message.tabIndex = -1;
    message.className = 'error-summary';
    message.setAttribute('role', 'alert');
    message.textContent = 'Não foi possível confirmar a gravação. Verifique a conexão e tente novamente.';
    form.prepend(message);
    message.focus();
  };
  document.addEventListener('htmx:sendError', transportFailure);
  document.addEventListener('htmx:timeout', transportFailure);
})();

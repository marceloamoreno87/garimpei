(() => {
  document.addEventListener('error', event => {
    if (!(event.target instanceof HTMLImageElement)) return;
    const img = event.target;
    img.hidden = true;
    const fallback = document.createElement('span');
    fallback.textContent = 'Imagem não disponível';
    fallback.setAttribute('role','img');
    fallback.setAttribute('aria-label',img.alt + ': imagem não disponível');
    img.parentElement.append(fallback);
  }, true);
  const region = () => document.querySelector('#exploration');
  const context = () => region()?.dataset.canonical || location.href;
  if (region()?.dataset.canonical) history.replaceState({}, '', region().dataset.canonical);
  const poll = () => { if (!document.hidden) window.htmx?.trigger(document.body,'exploration-poll'); };
  document.addEventListener('visibilitychange', poll);
  window.addEventListener('pageshow', poll);
  document.body.addEventListener('htmx:configRequest', event => {
    event.detail.headers['X-Exploration-Context'] = context();
  });
  document.body.addEventListener('htmx:beforeSwap', event => {
    const requestContext = event.detail.requestConfig?.headers['X-Exploration-Context'];
    if (!event.detail.target.isConnected || (requestContext && requestContext !== context())) {
      event.detail.shouldSwap = false;
      return;
    }
    if (event.detail.target.id === 'updates' && event.detail.xhr.status >= 400) {
      event.detail.shouldSwap = false;
      return;
    }
    if (event.detail.xhr.status >= 400) {
      event.detail.shouldSwap = false;
      const feedback = document.querySelector('#exploration-feedback');
      if (feedback) feedback.textContent = 'Não foi possível atualizar os valores. Tente novamente';
    }
  });
  document.body.addEventListener('htmx:afterSwap', event => {
    if (event.detail.target.id === 'updates' && region()?.dataset.detail) {
      region().querySelectorAll('[data-apply]').forEach(a => {
        a.href = region().dataset.refresh + '&aplicar=1';
        a.setAttribute('hx-get', a.href);
        a.setAttribute('hx-target', '#main');
        a.setAttribute('hx-select', '#main');
        a.setAttribute('hx-swap', 'outerHTML');
        window.htmx?.process(a);
      });
    }
    if (event.detail.target.id !== 'exploration') return;
    const root = region();
    if (root?.dataset.applied === 'true') {
      document.querySelector('#exploration-feedback').textContent = '';
      (root.querySelector('.offer-title') || root.querySelector('#results-title'))?.focus();
    }
  });
  document.addEventListener('keydown', event => {
    const tab = event.target.closest?.('.condition-tabs [role=tab]');
    if (!tab) return;
    const tabs = [...document.querySelectorAll('.condition-tabs [role=tab]')];
    const index = tabs.indexOf(tab);
    const moves = {ArrowRight:(index+1)%tabs.length, ArrowLeft:(index+tabs.length-1)%tabs.length, Home:0, End:tabs.length-1};
    if (!(event.key in moves)) return;
    event.preventDefault();
    // Native navigation also works without HTMX, preserving the selected revision.
    sessionStorage.setItem('condition-tab-focus','1');
    location.assign(tabs[moves[event.key]].href);
  });
})();

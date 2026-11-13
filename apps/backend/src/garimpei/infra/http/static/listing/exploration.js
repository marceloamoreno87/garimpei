(() => {
  if (window.garimpeiExplorationLoaded) return;
  window.garimpeiExplorationLoaded = true;
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
  let pendingFocus = null;
  document.body.addEventListener('htmx:beforeRequest', event => {
    if (event.detail.target?.id !== 'exploration') return;
    const active = document.activeElement;
    pendingFocus = event.detail.elt.matches('[role=tab]')
      ? {kind: 'tab'}
      : active?.id === 'exploration-search'
        ? {kind: 'search', start: active.selectionStart, end: active.selectionEnd}
        : {kind: 'results'};
    region()?.setAttribute('aria-busy', 'true');
  });
  document.body.addEventListener('htmx:afterRequest', event => {
    if (event.detail.target?.id === 'exploration') region()?.removeAttribute('aria-busy');
  });
  let loadedAt = new Date().toLocaleTimeString('pt-BR');
  const readingFailure = () => {
    const feedback = document.querySelector('#exploration-feedback');
    if (!feedback) return;
    feedback.dataset.readFailure = 'true';
    feedback.setAttribute('role', 'alert');
    const text = document.createTextNode(`Não foi possível atualizar. A leitura carregada às ${loadedAt} continua visível. `);
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'button secondary';
    retry.textContent = 'Tentar novamente';
    retry.addEventListener('click', () => {
      const statusUrl = region()?.dataset.statusUrl;
      if (window.htmx && statusUrl) window.htmx.ajax('GET', statusUrl, {target:'#updates', swap:'innerHTML'});
      else location.assign(context());
    });
    feedback.replaceChildren(text, retry);
  };
  for (const name of ['htmx:sendError', 'htmx:timeout']) {
    document.body.addEventListener(name, event => {
      const target = event.detail.target;
      const requestContext = event.detail.requestConfig?.headers['X-Exploration-Context'];
      if (requestContext && requestContext !== context()) return;
      if (target?.id === 'updates' || target?.id === 'exploration' || target?.closest?.('#exploration')) readingFailure();
    });
  }
  document.body.addEventListener('htmx:beforeSwap', event => {
    if (!['updates', 'exploration', 'main'].includes(event.detail.target?.id)) return;
    const requestContext = event.detail.requestConfig?.headers['X-Exploration-Context'];
    if (!event.detail.target.isConnected || (requestContext && requestContext !== context())) {
      event.detail.shouldSwap = false;
      return;
    }
    if (event.detail.target.id === 'updates' && event.detail.xhr.status >= 400) {
      event.detail.shouldSwap = false;
      readingFailure();
      return;
    }
    if (event.detail.xhr.status >= 400) {
      event.detail.shouldSwap = false;
      readingFailure();
    }
  });
  document.body.addEventListener('htmx:afterSwap', event => {
    if (region()?.dataset.applied === 'true' && ['main','exploration'].includes(event.detail.target.id)) loadedAt = new Date().toLocaleTimeString('pt-BR');
    const feedback = document.querySelector('#exploration-feedback');
    if (event.detail.target.id === 'updates' && feedback?.dataset.readFailure) {
      feedback.replaceChildren();
      delete feedback.dataset.readFailure;
    }
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
    if (pendingFocus) {
      const target = pendingFocus.kind === 'tab'
        ? root?.querySelector('[role=tab][aria-selected=true]')
        : pendingFocus.kind === 'search'
          ? root?.querySelector('#exploration-search')
          : root?.querySelector('#results-title');
      target?.focus({preventScroll: pendingFocus.kind === 'search'});
      if (pendingFocus.kind === 'search') target?.setSelectionRange(pendingFocus.start, pendingFocus.end);
      const count = root?.querySelector('#results-title')?.textContent;
      if (count && feedback) feedback.textContent = `Ofertas exibidas: ${count}`;
      pendingFocus = null;
    }
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

// Image transfer failures preserve the text and recovery controls already on this page.
document.addEventListener("error", event => {
  const target = event.target;
  if (!(target instanceof HTMLImageElement) || !target.matches("[data-media-image]")) return;
  target.hidden = true;
  const fallback = target.closest("figure, .offer-image")?.querySelector(".media-load-error");
  if (fallback) fallback.hidden = false;
}, true);

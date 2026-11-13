(() => {
  if (window.garimpeiProgressLoaded) return;
  window.garimpeiProgressLoaded = true;
  const feedback = message => {
    const target = document.getElementById('navigation-feedback');
    if (target) target.textContent = message;
  };
  const isProgress = event => event.detail.target?.closest('#navigation-progress');
  const fail = () => feedback(document.getElementById('navigation-title')
    ? 'Não foi possível atualizar o percurso. A última leitura continua disponível. Tente novamente.'
    : 'Não foi possível carregar o percurso. Tente carregar novamente abaixo.');
  for (const name of ['htmx:sendError', 'htmx:timeout']) {
    document.addEventListener(name, event => { if (isProgress(event)) fail(); });
  }
  document.addEventListener('htmx:beforeSwap', event => {
    if (isProgress(event) && event.detail.xhr.status >= 400) {
      event.detail.shouldSwap = false;
      fail();
    }
  });
  document.addEventListener('htmx:afterSwap', event => {
    if (event.detail.target.id === 'navigation-progress') {
      feedback('Percurso atualizado. Confira o horário desta leitura.');
    }
  });
})();

(() => {
  const feedback = () => document.querySelector('#operational-feedback');
  const fail = () => {
    const node = feedback();
    if (node) node.textContent = 'Não foi possível atualizar o acompanhamento. A última leitura continua visível. Tente novamente.';
  };
  document.body.addEventListener('htmx:beforeSwap', event => {
    if (event.detail.target?.id !== 'operational-status') return;
    if (event.detail.xhr.status >= 400) {
      event.detail.shouldSwap = false;
      fail();
    }
  });
  for (const name of ['htmx:sendError', 'htmx:timeout']) {
    document.body.addEventListener(name, event => {
      if (event.detail.target?.id === 'operational-status') fail();
    });
  }
})();

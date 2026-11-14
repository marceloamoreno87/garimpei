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

(() => {
  const feedback = () => document.getElementById('assistance-operation-feedback');
  document.body.addEventListener('htmx:beforeSwap', event => {
    if (event.detail.target?.id !== 'assistance-operation-feedback') return;
    if ([400, 403, 409, 422, 503].includes(event.detail.xhr.status)) {
      event.detail.shouldSwap = true;
      event.detail.isError = false;
    }
  });
  document.body.addEventListener('htmx:afterSettle', event => {
    if (event.detail.target?.id === 'assistance-operation-feedback') feedback()?.focus();
  });
  for (const name of ['htmx:sendError', 'htmx:timeout']) {
    document.body.addEventListener(name, event => {
      if (event.detail.target?.id !== 'assistance-operation-feedback') return;
      const node = feedback();
      if (!node) return;
      node.textContent = 'Não foi possível confirmar a explicação. O diagnóstico anterior continua disponível. Tente novamente.';
      node.focus();
    });
  }
})();

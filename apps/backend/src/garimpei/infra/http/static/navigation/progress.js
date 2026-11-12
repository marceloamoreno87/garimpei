(() => {
  function feedback(message) {
    const target = document.getElementById('navigation-feedback');
    if (target) target.textContent = message;
  }
  document.addEventListener('htmx:sendError', event => {
    if (!event.detail.elt.closest('#navigation-progress')) return;
    feedback('Não foi possível atualizar o percurso. A última leitura continua disponível. Tente novamente.');
  });
  document.addEventListener('htmx:afterSwap', event => {
    if (event.detail.target.id === 'navigation-progress') {
      feedback('Percurso atualizado. Confira o horário desta leitura.');
    }
  });
})();

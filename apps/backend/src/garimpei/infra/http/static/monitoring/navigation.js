(() => {
  if (window.garimpeiNavigationLoaded) return;
  window.garimpeiNavigationLoaded = true;
  const initialize = () => {
    const button = document.querySelector('.navigation-toggle');
    const navigation = document.getElementById('primary-navigation');
    if (!button || !navigation || button.dataset.ready) return;
    button.dataset.ready = 'true';
    const mobile = matchMedia('(max-width: 720px)');
    const show = expanded => {
      navigation.hidden = !expanded;
      button.setAttribute('aria-expanded', String(expanded));
    };
    const adapt = () => {
      button.hidden = !mobile.matches;
      if (mobile.matches && navigation.contains(document.activeElement)) button.focus();
      show(!mobile.matches);
    };
    button.addEventListener('click', () => show(navigation.hidden));
    navigation.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !mobile.matches) return;
      show(false);
      button.focus();
    });
    mobile.addEventListener('change', adapt);
    adapt();
  };
  initialize();
  document.addEventListener('htmx:afterSwap', initialize);
})();

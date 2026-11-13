// Keep a keyboard user's current action stable while background status refreshes.
document.addEventListener('htmx:beforeSwap', (event) => {
  const target = event.detail.target;
  if (target && target.id === 'robot-control' && target.contains(document.activeElement)) {
    event.preventDefault();
  }
});

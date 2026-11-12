(() => {
  const families = {
    generation: ["playstation5", "switch"],
    edition: ["playstation5", "iphone", "xbox", "camera"],
    capacity: ["playstation5", "iphone", "xbox", "switch", "graphics_card"],
    brand: ["camera", "television", "headphone"],
    memory_type: ["graphics_card"],
  };
  for (const form of document.querySelectorAll(".identity-form")) {
    const select = form.elements.namedItem("family");
    if (!select) continue;
    const update = () => {
      for (const [name, supported] of Object.entries(families)) {
        const field = form.elements.namedItem(name);
        const container = field?.closest("[data-identity-field]");
        if (!field || !container) continue;
        const visible = !select.value || supported.includes(select.value);
        container.hidden = !visible;
        field.disabled = !visible;
      }
    };
    select.addEventListener("change", update);
    update();
  }
})();

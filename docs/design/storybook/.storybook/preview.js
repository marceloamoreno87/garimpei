import '../../tokens.css';
import '../../components/components.css';
import '../../prototypes/prototype.css';

export default {
  parameters: { layout: 'padded' },
  globalTypes: {
    theme: {
      description: 'Tema dos mesmos tokens do protótipo',
      toolbar: { title: 'Tema', icon: 'paintbrush', items: [
        { value: 'editorial', title: 'Editorial' },
        { value: 'compact', title: 'Comparação' },
        { value: 'night', title: 'Mesa de análise' },
      ] },
    },
  },
  initialGlobals: { theme: 'editorial' },
  decorators: [(story, context) => {
    document.documentElement.lang = 'pt-BR';
    document.documentElement.dataset.variant = context.globals.theme;
    document.documentElement.style.colorScheme = context.globals.theme === 'night' ? 'dark' : 'light';
    return story();
  }],
};

export default {
  stories: ['../stories/**/*.stories.js'],
  framework: '@storybook/html-vite',
  staticDirs: [{ from: '../../prototypes/assets', to: '/assets' }],
  core: { disableTelemetry: true },
};

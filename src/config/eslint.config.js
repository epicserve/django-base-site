const js = require('@eslint/js');
const globals = require('globals');

const isDevMode = process.env.NODE_ENV === 'development';

module.exports = [
  js.configs.recommended,
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      // Allow console.error or console.warn in production and no warnings in development
      'no-console': isDevMode ? 'off' : ['error', { allow: ['warn', 'error'] }],

      // Allow debugger in development
      'no-debugger': isDevMode ? 'off' : 'error',

      // just one var declaration per function
      'one-var': ['error', 'always'],

      'max-len': ['error', { code: 120 }],
    },
  },
  {
    ignores: ['public/static/', 'collected_static/', 'htmlcov/', 'src/config/'],
  },
];

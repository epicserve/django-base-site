import globals from 'globals';
import js from '@eslint/js';
import pluginVue from 'eslint-plugin-vue';

const isDevMode = process.env.NODE_ENV === 'development';

export default [
  {
    ignores: ['public/static/', 'collected_static/', 'htmlcov/', 'frontend/config/'],
  },

  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],

  {
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
    rules: {
      'no-console': isDevMode ? 'off' : ['error', { allow: ['warn', 'error'] }],
      'no-debugger': isDevMode ? 'off' : 'error',
      'one-var': ['error', 'always'],
      'max-len': ['error', { code: 120 }],
      'no-underscore-dangle': ['error', { allow: ['__addToast'] }],
      'vue/no-v-for-template-key': 'off',
    },
  },

  {
    files: ['**/*.vue'],
    rules: {
      'one-var': 'off',
      'no-param-reassign': ['error', { props: false }],
      'max-len': ['error', { code: 120, ignorePattern: '\\s+class=' }],
    },
  },
];

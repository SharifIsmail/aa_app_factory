import js from '@eslint/js';
import tsParser from '@typescript-eslint/parser';
import pluginVitest from '@vitest/eslint-plugin';
import prettierConfig from '@vue/eslint-config-prettier';
import vueTsEslintConfig from '@vue/eslint-config-typescript';
import pluginPlaywright from 'eslint-plugin-playwright';
import pluginVue from 'eslint-plugin-vue';
import vueParser from 'vue-eslint-parser';

export default [
  js.configs.recommended,
  ...vueTsEslintConfig(),
  ...pluginVue.configs['flat/base'],
  ...pluginVue.configs['flat/strongly-recommended'],
  {
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
      },
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        node: true,
      },
    },
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'vue/no-multiple-template-root': 'off', // Vue 3 supports multiple roots
      'vue/camelcase': 'error',
      'vue/component-name-in-template-casing': [
        'error',
        'PascalCase',
        {
          registeredComponentsOnly: false,
        },
      ],
      'vue/no-undef-components': 'error',
      'vue/block-order': [
        'error',
        {
          order: ['i18n', 'script', 'template', 'style'],
        },
      ],
    },
  },

  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**'],
  },

  ...pluginVue.configs['flat/strongly-recommended'],

  {
    name: 'app/common-components-rules',
    files: ['src/common/components/**/*.vue'],
    rules: {
      'vue/multi-word-component-names': 'off', // Allow single-word for reusable components
    },
  },

  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/__tests__/*'],
  },

  {
    ...pluginPlaywright.configs['flat/recommended'],
    files: ['e2e/**/*.{test,spec}.{js,ts,jsx,tsx}'],
  },
  prettierConfig,
];

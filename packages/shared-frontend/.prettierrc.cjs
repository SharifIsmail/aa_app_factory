/* eslint-disable @typescript-eslint/no-require-imports */
/* eslint-disable no-undef */
const prettierConfig = require('@aleph-alpha/prettier-config-frontend');

module.exports = {
  ...prettierConfig,
  htmlWhitespaceSensitivity: 'css',
  // 'prettier-plugin-tailwindcss' should be imported after '@trivago/prettier-plugin-sort-imports'
  plugins: ['@trivago/prettier-plugin-sort-imports'],
};

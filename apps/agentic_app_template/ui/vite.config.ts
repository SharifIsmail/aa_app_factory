import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite';
import federation from '@originjs/vite-plugin-federation';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { resolve } from 'path';
import UnoCSS from 'unocss/vite';
import { defineConfig } from 'vite';
import vueDevTools from 'vite-plugin-vue-devtools';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    federation({
      name: 'application',
      filename: 'usecase.js',
      exposes: {
        './Usecase': './src/App.vue',
      },
      shared: {
        vue: {},
        pinia: {},
        'vue-router': {},
        '@vueuse/core': {},
        'vue-i18n': { version: '*' },
      },
    }),
    VueI18nPlugin({
      include: [resolve(__dirname, './src/locales/*.json')],
    }),
    UnoCSS(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    target: 'esnext',
    cssCodeSplit: false,
  },
});

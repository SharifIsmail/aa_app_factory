import App from './App.vue';
import i18n from './i18n';
import AADesignSystem from '@aleph-alpha/ds-components-vue';
import '@unocss/reset/tailwind.css';
import { createPinia } from 'pinia';
import 'virtual:uno.css';
import { createApp } from 'vue';

const app = createApp(App);

app.use(i18n);
// @ts-expect-error AADesignSystem is a plugin, but it's not typed as such in the package.
app.use(AADesignSystem);
app.use(createPinia());

app.mount('#app');

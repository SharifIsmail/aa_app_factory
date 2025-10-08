import App from './App.vue';
import i18n from './i18n';
import AADesignSystem from '@aleph-alpha/ds-components-vue';
import '@unocss/reset/tailwind.css';
import { createPinia } from 'pinia';
import { createPersistedState } from 'pinia-plugin-persistedstate';
import 'virtual:uno.css';
import { createApp } from 'vue';

const app = createApp(App);

const pinia = createPinia();
pinia.use(createPersistedState());
app.use(pinia);

app.use(i18n);
// @ts-expect-error AADesignSystem is a plugin, but it's not typed as such in the package.
app.use(AADesignSystem);

app.mount('#app');

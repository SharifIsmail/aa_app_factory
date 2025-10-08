import { createI18n } from 'vue-i18n';

const DEFAULT_APP_LOCALE = 'en';

// The setup of i18n is only relevant when running the app in dev mode
export const i18n = createI18n({
  locale: DEFAULT_APP_LOCALE,
  fallbackLocale: DEFAULT_APP_LOCALE,
  legacy: false,
  messages: {
    en: {},
    de: {},
  },
  fallbackWarn: false,
  missingWarn: true,
});

export default i18n;

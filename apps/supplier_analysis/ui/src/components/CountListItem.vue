<i18n src="src/locales/locales.json" />
<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const URLS: Record<string, { url: string; text: string }> = {
  getting_started_documentation: {
    url: 'https://docs.aleph-alpha.com/products/pharia-studio/how-to/getting-started-with-pharia-applications/',
    text: t('LOCALES.GET_STARTED.getting_started_documentation'),
  },
  cli_guide: {
    url: 'https://docs.aleph-alpha.com/products/pharia-studio/how-to/pharia-applications-quick-start/',
    text: t('LOCALES.GET_STARTED.cli_guide'),
  },
  kernel_skills_documentation: {
    url: 'https://docs.aleph-alpha.com/products/pharia-studio/how-to/getting-started-with-kernel-skills/',
    text: t('LOCALES.GET_STARTED.kernel_skills_documentation'),
  },
  answers: {
    url: 'https://docs.aleph-alpha.com/products/pharia-studio/references/pharia-applications-troubleshooting/',
    text: t('LOCALES.GET_STARTED.answers'),
  },
  feedback: {
    url: 'https://aleph-alpha.atlassian.net/servicedesk/customer/portal/14',
    text: t('LOCALES.GET_STARTED.feedback'),
  },
};

const props = defineProps<{
  countText: string;
  countItemTitle: string;
  textId: number;
}>();

const translatedText = computed(() => {
  let textContent = t(`LOCALES.GET_STARTED.item-text-${props.textId}`);
  Object.keys(URLS).forEach((key) => {
    const decoratedText = `<a href="${URLS[key].url}" target="_blank" rel="noopener noreferrer" class="underline">${URLS[key].text}</a>`;
    textContent = textContent.replace(`_${key}_`, decoratedText);
  });

  return textContent;
});
</script>

<template>
  <div class="flex flex-row gap-4">
    <div class="relative inline-block">
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="12.1646" cy="12" r="11.5" fill="#CCE804" stroke="#DBDBE9" />
        <text
          x="50%"
          y="50%"
          fill="black"
          dominant-baseline="middle"
          text-anchor="middle"
          font-family="inherit"
          class="text-xs"
        >
          {{ countText }}
        </text>
      </svg>
    </div>
    <div>
      <span class="text-core-content-secondary font-bold"> {{ countItemTitle }} </span>
      <span v-html="translatedText"></span>
    </div>
  </div>
</template>

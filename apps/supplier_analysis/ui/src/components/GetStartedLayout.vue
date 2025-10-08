<i18n src="src/locales/locales.json" />
<script setup lang="ts">
import CountListItem from '@/components/CountListItem.vue';
import { useQuoteStore } from '@/stores/useQuoteStore.ts';
import { AaText, AaButton } from '@aleph-alpha/ds-components-vue';
import { range } from 'lodash';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  title: string;
  subtitle: string;
  countListItems: { title: string; textId: number }[];
}>();

const store = useQuoteStore();
</script>

<template>
  <div class="flex h-full w-full items-center justify-center">
    <div class="max-w-208.5 flex flex-row gap-12">
      <div class="flex-0">
        <slot name="illustration" />
      </div>
      <div class="flex flex-col justify-center gap-5">
        <div class="flex flex-col gap-6">
          <AaText color="text-core-content-primary" size="3xl" weight="bold" wrap="prewrap">
            {{ title }}
          </AaText>
          <AaText>
            {{ subtitle }}
          </AaText>
          <div class="flex flex-col gap-6">
            <CountListItem
              v-for="idx in range(0, countListItems.length, 1)"
              :key="idx"
              :count-item-title="countListItems[idx].title"
              :text-id="countListItems[idx].textId"
              :count-text="(idx + 1).toString()"
            />
          </div>
          <div class="gap-M flex flex-col bg-white p-4">
            <AaText weight="bold" color="text-core-content-secondary">
              {{ t('LOCALES.quote-generator') }}
            </AaText>
            <textarea
              class="text-core-content-secondary resize-none"
              rows="2"
              :value="store.quoteResponse"
            />
            <div class="place-self-end">
              <AaButton
                :append-icon="
                  store.requestIsBeingProcessed
                    ? 'i-material-symbols-progress-activity animate-spin'
                    : 'i-material-symbols-cached'
                "
                @click="store.generateQuote"
              >
                {{ t('LOCALES.generate-new-quote') }}
              </AaButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

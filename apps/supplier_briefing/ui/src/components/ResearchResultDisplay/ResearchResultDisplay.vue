<script setup lang="ts">
import AnswerDisplay from './AnswerDisplay.vue';
import StepsDisplay from './StepsDisplay.vue';
import type { SerializedPandasObject, ExplainedStep } from '@/types';
import { AaTabs, AaTab, AaText } from '@aleph-alpha/ds-components-vue';

defineProps<{
  question: string;
  answer: string | any;
  timestamp?: string;
  pandasObjectsData?: Record<string, SerializedPandasObject> | null;
  explainedSteps?: ExplainedStep[] | null;
  resultsData?: Record<string, any> | null;
  isSearching?: boolean;
  isFailed?: boolean;
}>();
</script>

<template>
  <div class="research-result mx-auto mb-6 w-4/5">
    <div class="mb-6">
      <h3 class="text-core-content-primary mb-3 text-lg font-semibold">Anfrage</h3>
      <p class="text-core-content-primary">{{ question }}</p>
    </div>

    <AaTabs>
      <AaTab label="Ergebnis" name="answer">
        <div
          v-if="isFailed"
          class="border-core-border-critical bg-core-surface-critical mb-4 flex items-start gap-3 rounded-md border p-4"
        >
          <span
            class="i-material-symbols-error-outline-rounded text-core-content-critical text-xl"
          ></span>
          <div class="flex-1">
            <AaText size="sm" weight="semibold" class="text-core-content-critical">Fehler</AaText>
            <AaText size="sm" class="text-core-content-critical">
              Etwas ist schiefgelaufen. Bitte versuchen Sie es später erneut.
            </AaText>
          </div>
        </div>
        <AnswerDisplay
          v-if="!isFailed"
          :answer="answer"
          :is-searching="isSearching"
          :pandas-objects-data="pandasObjectsData"
          :explained-steps="explainedSteps"
          :results-data="resultsData"
        />
      </AaTab>
      <AaTab v-if="!isSearching && !isFailed" label="Detaillierte Schritte" name="steps">
        <StepsDisplay :explained-steps="explainedSteps" :is-searching="isSearching" />
      </AaTab>
    </AaTabs>

    <div v-if="timestamp" class="text-core-content-secondary mt-4 text-xs">
      {{ timestamp }}
    </div>
  </div>
</template>

<style scoped>
.research-result {
  transition: all 0.2s ease-in-out;
}
</style>

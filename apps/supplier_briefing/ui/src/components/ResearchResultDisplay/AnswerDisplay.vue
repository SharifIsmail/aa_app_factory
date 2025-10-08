<script setup lang="ts">
import AnswerDisplayThoughts from './AnswerDisplayThoughts.vue';
import DataFoundationDisplay from './DataFoundationDisplay.vue';
import type { SerializedPandasObject, ExplainedStep } from '@/types';
import { AaCircularLoading } from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

const props = defineProps<{
  answer: string | any;
  isSearching?: boolean;
  pandasObjectsData?: Record<string, SerializedPandasObject> | null;
  explainedSteps?: ExplainedStep[] | null;
  resultsData?: Record<string, any> | null;
}>();

const displayAnswer = computed(() => {
  if (!props.answer) return 'Keine Ergebnisse abgerufen';
  return props.answer;
});
</script>

<template>
  <div class="mb-6">
    <AnswerDisplayThoughts :explained-steps="explainedSteps" />
    <div
      v-if="isSearching"
      class="align-flex-start text-core-content-placeholder flex gap-2 text-xs italic"
    >
      {{ props.answer || 'Suche läuft' }} <AaCircularLoading />
    </div>
    <div v-if="!isSearching" class="align-flex-start text-core-content-primary flex gap-2 text-sm">
      {{ displayAnswer }}
    </div>
  </div>

  <DataFoundationDisplay :pandas-objects-data="pandasObjectsData" :results-data="resultsData" />
</template>

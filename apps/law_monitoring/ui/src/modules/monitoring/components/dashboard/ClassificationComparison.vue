<script setup lang="ts">
import FileSuccessIcon from '@/assets/icons/FileSuccess.svg?inline';
import { AaText } from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

const props = defineProps<{
  recallValue: number;
}>();

const computedRecallValue = computed(() => {
  return props.recallValue ? Math.round(props.recallValue * 100) || 0 : 0;
});
</script>

<template>
  <div class="bg-core-bg-primary flex h-fit flex-col rounded-lg p-5">
    <div class="flex flex-col gap-1">
      <AaText class="text-core-content-secondary text-base font-bold">
        Classification accuracy
      </AaText>
      <AaText class="text-core-content-tertiary text-sm">
        % of all acts classified “Relevant” by both AI and humans
      </AaText>
    </div>

    <div class="flex flex-row p-8">
      <img :src="FileSuccessIcon" alt="File Success Icon" class="h-23" />
      <AaText class="text-semantic-content-success-label mb-auto mt-auto p-2 text-3xl font-bold">
        {{ computedRecallValue == 0 ? 'N/A' : computedRecallValue + '%' }}
      </AaText>
    </div>
  </div>
</template>

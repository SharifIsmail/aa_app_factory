<script setup lang="ts">
import UploadFilesIcon from '@/assets/icons/UploadFiles.svg?inline';
import { type DateRange } from '@/modules/monitoring/types';
import { AaText } from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

const props = defineProps<{
  totalLegalActs: number;
  totalEvaluations: number;
  dateRange: DateRange;
}>();

const unreviewedActs = computed(() => {
  return props.totalLegalActs - props.totalEvaluations;
});
</script>

<template>
  <div
    class="border-core-border-default bg-core-bg-primary p-t-3 p-r-4 p-b-3 p-l-4 flex flex-col rounded-l-lg border border-r-0"
  >
    <div class="flex flex-col gap-1 p-1">
      <AaText class="text-core-content-secondary text-base font-bold">
        Legal acts classification overview
      </AaText>
      <AaText class="text-core-content-tertiary text-sm">
        Number of released acts and progress on reviews
      </AaText>
    </div>
    <div class="flex flex-row gap-2 p-5">
      <img :src="UploadFilesIcon" alt="Upload Files Icon" class="h-23" />
      <div class="flex flex-col gap-2 p-2">
        <AaText class="text-core-content-secondary text-2xl font-bold">
          {{ totalLegalActs }}
        </AaText>
        <AaText class="text-core-content-secondary text-sm">total acts</AaText>
      </div>

      <div class="flex flex-col gap-2 p-2">
        <AaText class="text-core-content-secondary text-2xl font-bold">
          {{ props.totalEvaluations }}
        </AaText>
        <AaText class="text-core-content-secondary text-sm">acts reviewed</AaText>
      </div>
      <div class="flex flex-col gap-2 p-2">
        <AaText class="text-core-content-secondary text-2xl font-bold">
          {{ unreviewedActs }}
        </AaText>
        <AaText class="text-core-content-secondary text-sm">acts unreviewed</AaText>
      </div>
    </div>
  </div>
</template>

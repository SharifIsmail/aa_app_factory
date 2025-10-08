<script setup lang="ts">
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore.ts';
import { AaText, AaButton, AaTooltip, AaSkeletonLoading } from '@aleph-alpha/ds-components-vue';
import type { PreprocessedLaw } from 'src/modules/monitoring/types';
import { computed, ref } from 'vue';

interface Props {
  overview: string;
  laws: PreprocessedLaw[];
  activeFilter: string | null;
}

interface Emits {
  (e: 'set-status-filter', status: string): void;

  (e: 'clear-filter'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const helpIconRef = ref<HTMLElement | null>(null);

const statusCounts = computed(() => {
  const counts = {
    RAW: 0,
    PROCESSING: 0,
    PROCESSED: 0,
    FAILED: 0,
  };

  props.laws.forEach((law) => {
    if (law.status in counts) {
      counts[law.status as keyof typeof counts]++;
    }
  });

  return counts;
});

const setStatusFilter = (status: string) => {
  emit('set-status-filter', status);
};

const clearFilter = () => {
  emit('clear-filter');
};
const lawCoordinatorStore = useLawCoordinatorStore();
</script>

<template>
  <div
    v-if="
      lawCoordinatorStore.isLoading ||
      lawCoordinatorStore.isSearching ||
      lawCoordinatorStore.isLoadingLawsByDate
    "
    class="w-128 h-10"
  >
    <AaSkeletonLoading class="rounded"></AaSkeletonLoading>
  </div>
  <div v-else-if="laws.length > 0">
    <!-- Filter indicator - subtle with light background -->
    <div v-if="activeFilter" class="bg-core-bg-secondary mb-4 rounded px-3 py-2">
      <div class="flex items-center gap-2 text-sm">
        <span class="text-core-content-primary font-medium">
          {{
            activeFilter === 'RAW'
              ? 'Showing Acts Awaiting Analysis'
              : activeFilter === 'PROCESSING'
                ? 'Showing Acts Currently Processing'
                : activeFilter === 'PROCESSED'
                  ? 'Showing Acts with Completed Analyses'
                  : 'Showing Failed Acts'
          }}
        </span>
        <AaButton @click="clearFilter" variant="outline"> Reset Filter</AaButton>
      </div>
    </div>

    <!-- AI Analyses Status Panel -->
    <div v-else class="bg-core-bg-secondary mb-4 rounded border py-2 pl-2 pr-4">
      <div class="flex flex-wrap items-center justify-between gap-3 text-sm">
        <div class="flex flex-wrap items-center gap-1">
          <i class="i-material-symbols-info-outline"></i>
          <AaText class="p-[7px]" weight="bold"> {{ overview }} </AaText>
          <span class="mx-0 hidden sm:mx-2 sm:inline">|</span>
          <AaButton
            variant="text"
            v-if="statusCounts.PROCESSED > 0"
            :class="{ 'font-medium': activeFilter === 'PROCESSED' }"
            @click="setStatusFilter('PROCESSED')"
          >
            <div class="text-semantic-content-success-label flex gap-1">
              <i class="i-material-symbols-check-circle-outline"></i>
              {{ statusCounts.PROCESSED }} <span class="hidden lg:inline">Ready</span>
            </div>
          </AaButton>

          <AaButton
            variant="text"
            v-if="statusCounts.PROCESSING > 0"
            :class="{ 'font-medium': activeFilter === 'PROCESSING' }"
            @click="setStatusFilter('PROCESSING')"
          >
            <div class="flex gap-1 text-amber-600">
              <i class="i-material-symbols-pending-outline"></i>
              {{ statusCounts.PROCESSING }} <span class="hidden lg:inline">Analyzing</span>
            </div>
          </AaButton>

          <AaButton
            variant="text"
            v-if="statusCounts.RAW > 0"
            :class="{ 'font-medium': activeFilter === 'RAW' }"
            @click="setStatusFilter('RAW')"
          >
            <div class="text-semantic-content-info-soft flex gap-1">
              <i class="i-material-symbols-schedule-outline"></i>
              {{ statusCounts.RAW }} <span class="hidden lg:inline">Awaiting</span>
            </div>
          </AaButton>

          <AaButton
            variant="text"
            v-if="statusCounts.FAILED > 0"
            :class="{ 'font-medium': activeFilter === 'FAILED' }"
            @click="setStatusFilter('FAILED')"
          >
            <div class="text-semantic-content-error-soft flex cursor-pointer items-center gap-1">
              <i class="i-material-symbols-cancel-outline"></i>
              {{ statusCounts.FAILED }} <span class="hidden lg:inline">Failed</span>
            </div>
          </AaButton>
        </div>

        <div>
          <span
            ref="helpIconRef"
            class="flex h-5 w-5 cursor-help items-center justify-center rounded-full text-xs font-bold text-gray-600"
          >
            <i class="i-material-symbols-help h-full w-full"></i>
          </span>

          <AaTooltip :anchor="helpIconRef" placement="bottom-end" :z-index="10" class="w-80">
            <div class="space-y-2">
              <div class="font-medium">What does this mean?</div>
              <div class="space-y-1">
                <div>
                  <strong> Ready:</strong> Legal acts successfully analyzed and ready for review
                </div>
                <div><strong>Analyzing:</strong> Legal acts being processed by our AI system</div>
                <div><strong>Awaiting:</strong> Legal acts queued for AI processing</div>
                <div>
                  <strong>Failed:</strong> Legal acts that encountered errors during processing
                </div>
              </div>
            </div>
          </AaTooltip>
        </div>
      </div>
    </div>
  </div>
</template>

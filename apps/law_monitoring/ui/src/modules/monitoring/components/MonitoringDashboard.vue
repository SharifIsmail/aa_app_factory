<script setup lang="ts">
import AffectedDepartmentsWidget from './dashboard/AffectedDepartmentsWidget.vue';
import DashboardOverview from './dashboard/DashboardOverview.vue';
import TimelineChartsWidget from './dashboard/TimelineChartsWidget.vue';
import EurovocHeatmapWidget from './dashboard/eurovoc_heatmap/EurovocHeatmapWidget.vue';

// import { useDashboardStore } from '@/modules/monitoring/stores/dashboardStore';
// import { useLawDataStore } from '@/modules/monitoring/stores/lawDataStore';
// import { OfficialJournalSeries } from '@/modules/monitoring/types';
// import { AaText, AaToggleButtons } from '@aleph-alpha/ds-components-vue';
// import { computed } from 'vue';

interface Props {
  height: number;
}

//todo: add filter height back
// const FILTER_HEIGHT = 80;
const FILTER_HEIGHT = 0;
const props = defineProps<Props>();

// const dashboardStore = useDashboardStore();
// const lawDataStore = useLawDataStore();

// const journalSeriesToggleOptions = computed(() => {
//   const isDisabled = dashboardStore.isLoading || lawDataStore.isLoadingDates;
//   return [
//     {
//       value: null,
//       label: 'All Acts',
//       disabled: isDisabled,
//     },
//     {
//       value: OfficialJournalSeries.L_SERIES,
//       label: 'L-Series Only',
//       disabled: isDisabled,
//     },
//   ];
// });

// const handleJournalSeriesChange = (value: string | null) => {
//   dashboardStore.setJournalSeriesFilter(value as OfficialJournalSeries | null);
// };
</script>

<template>
  <div :style="{ height: `${props.height}px` }">
    <!-- <div class="flex items-center gap-3" :style="{ height: `${FILTER_HEIGHT}px` }">
      <AaText class="text-core-content-tertiary text-sm font-bold">Journal Series</AaText>
      <AaToggleButtons
        :model-value="dashboardStore.currentJournalSeries"
        :options="journalSeriesToggleOptions"
        size="small"
        @update:model-value="handleJournalSeriesChange"
      />
    </div> -->
    <div
      class="flex flex-col gap-5 overflow-y-auto"
      :style="{ height: `${props.height - FILTER_HEIGHT}px` }"
    >
      <DashboardOverview />
      <TimelineChartsWidget />
      <div class="m-b-4 flex w-full gap-5">
        <div class="w-55/100">
          <AffectedDepartmentsWidget />
        </div>
        <div class="w-45/100">
          <EurovocHeatmapWidget />
        </div>
      </div>
    </div>
  </div>
</template>

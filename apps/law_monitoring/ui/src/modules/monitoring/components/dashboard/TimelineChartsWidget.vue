<script setup lang="ts">
import ChartSkeleton from './ChartSkeleton.vue';
import TimelineChart from './TimelineChart.vue';
import { useWidgetExport, EXPORT_FORMAT } from '@/@core/composables/useWidgetExport';
import { useAppStore } from '@/modules/monitoring/stores/appStore';
import { useDashboardStore } from '@/modules/monitoring/stores/dashboardStore';
import { useLawDataStore } from '@/modules/monitoring/stores/lawDataStore';
import { type DateRange, MonitoringTab } from '@/modules/monitoring/types';
import { AaText, AaToggleButtons, AaIconButton } from '@aleph-alpha/ds-components-vue';
import { ChartType } from '@app-factory/shared-frontend/components';
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';
import { ref, computed, watch } from 'vue';

// Initialize stores
const dashboardStore = useDashboardStore();
const lawDataStore = useLawDataStore();
const appStore = useAppStore();
const chartType = ref<ChartType>(ChartType.BAR);

const { handleExport } = useWidgetExport({
  containerSelector: '.timeline-chart-container',
  baseFilename: 'timeline-chart',
  exclusionAttributes: ['data-export-ignore'],
});

const chartTypeOptions = computed(() => {
  const isDisabled = dashboardStore.isLoading || lawDataStore.isLoadingDates;
  return [
    {
      value: ChartType.BAR,
      label: 'Bar Chart',
      icon: 'i-material-symbols-bar-chart',
      disabled: isDisabled,
    },
    {
      value: ChartType.LINE,
      label: 'Line Chart',
      icon: 'i-material-symbols-show-chart',
      disabled: isDisabled,
    },
  ];
});

const chartTitleText = computed(() => {
  return chartType.value === ChartType.BAR ? 'Legal acts review' : 'Legal acts relevance';
});

const chartLabelText = computed(() => {
  return chartType.value === ChartType.BAR
    ? 'How many were released this period and their review status'
    : 'How many were released this period and how many turned out relevant';
});

const selectedDateRange = ref<DateRange | null>(null);

const dateRangeDisplay = computed(() => {
  if (selectedDateRange.value) {
    const [start, end] = selectedDateRange.value;
    const startDate = start.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
    const endDate = end.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
    return `${startDate} - ${endDate}`;
  }
  return 'Last 10 Days';
});

const fetchTimelineData = async (
  dateRange: DateRange | null = selectedDateRange.value,
  skipLoading = false
) => {
  const availableDates = lawDataStore.availableDates;
  const endDate = availableDates[availableDates.length - 1];
  const startDate =
    availableDates.length > 10 ? availableDates[availableDates.length - 10] : availableDates[0];

  const startDateObj = new Date(startDate);
  const endDateObj = new Date(endDate);

  if (dateRange) {
    await dashboardStore.fetchTimelineForDateRange(
      dateRange,
      dashboardStore.currentJournalSeries || undefined,
      skipLoading
    );
  } else {
    await dashboardStore.fetchTimelineForDateRange(
      [startDateObj, endDateObj],
      dashboardStore.currentJournalSeries || undefined,
      skipLoading
    );
  }
};

watch(
  () => lawDataStore.availableDates,
  (newDates) => {
    if (newDates && newDates.length > 0) {
      fetchTimelineData();
    }
  },
  { immediate: true }
);

watch(
  () => appStore.activeTab,
  async (newTab, oldTab) => {
    if (newTab === MonitoringTab.DASHBOARD && oldTab !== MonitoringTab.DASHBOARD) {
      await fetchTimelineData();
    }
  }
);

watch(
  () => dashboardStore.currentJournalSeries,
  () => {
    fetchTimelineData(undefined, true);
  }
);

const handleDateRangeChange = async (dateRange: DateRange | null) => {
  selectedDateRange.value = dateRange;
  await fetchTimelineData(dateRange);
};
</script>

<template>
  <div class="timeline-chart-container bg-core-bg-primary flex flex-col gap-2 rounded-lg p-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex flex-col gap-1">
        <AaText class="text-core-content-secondary text-base font-bold">
          {{ chartTitleText }} ({{ dateRangeDisplay }})
        </AaText>
        <AaText class="text-core-content-tertiary text-sm">
          {{ chartLabelText }}
        </AaText>
      </div>

      <div class="flex items-center gap-2">
        <VueDatePicker
          :model-value="selectedDateRange"
          range
          auto-apply
          :enable-time-picker="false"
          :min-date="lawDataStore.firstDate"
          :max-date="lawDataStore.lastDate"
          :disabled-dates="lawDataStore.disabledDates"
          placeholder="Select date range"
          format="dd.MM.yyyy"
          range-separator=" - "
          clearable
          :loading="lawDataStore.isLoadingDates"
          :disabled="lawDataStore.isLoadingDates"
          @update:model-value="handleDateRangeChange"
          class="w-64"
          data-export-ignore
        />
        <AaToggleButtons
          v-model="chartType"
          :options="chartTypeOptions"
          size="small"
          data-export-ignore
        />
        <AaIconButton
          variant="ghost"
          icon="i-material-symbols-download"
          size="medium"
          label="Export as PNG"
          tooltip-text="Export as PNG"
          @click="handleExport(EXPORT_FORMAT.PNG)"
          data-export-ignore
        />
      </div>
    </div>

    <div class="chart-container">
      <div v-if="dashboardStore.isLoading || lawDataStore.isLoadingDates" class="h-full">
        <ChartSkeleton />
      </div>

      <div v-else-if="dashboardStore.currentTimelineData.length > 0" class="h-full">
        <TimelineChart
          :timeline-data="dashboardStore.currentTimelineData"
          :chart-type="chartType"
          :date-range-display="dateRangeDisplay"
        />
      </div>

      <div v-else class="flex h-full items-center justify-center">
        <div class="text-center">
          <AaText class="text-core-content-secondary mb-2 text-lg"
            >No timeline data available</AaText
          >
          <AaText class="text-core-content-secondary text-sm opacity-75"
            >Please try refreshing or check your connection</AaText
          >
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  height: 350px;
  position: relative;
}
</style>

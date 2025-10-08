<script setup lang="ts">
import EurovocTopicsDialog from './EurovocTopicsDialog.vue';
import WidgetExportButton from '@/@core/components/WidgetExportButton.vue';
import { useWidgetExport, EXPORT_FORMAT } from '@/@core/composables/useWidgetExport';
import { useAppStore } from '@/modules/monitoring/stores/appStore';
import { useDashboardStore } from '@/modules/monitoring/stores/dashboardStore';
import { type DateRange, MonitoringTab } from '@/modules/monitoring/types';
import {
  AaText,
  AaSelect,
  AaButton,
  type AaSelectOption,
  type AaSelectModelValue,
} from '@aleph-alpha/ds-components-vue';
import {
  HeatmapVisualization,
  HeatmapCell,
  HeatmapGrid,
  HeatmapLegend,
  type HeatmapDataItem,
} from '@app-factory/shared-frontend/components';
import { downloadFile } from '@app-factory/shared-frontend/utils';
import { ref, computed, watch, onMounted } from 'vue';

enum TimelineOptions {
  TODAY = 'today',
  WEEK = 'week',
  MONTH = 'month',
}

const { handleExport: handleWidgetExport } = useWidgetExport({
  containerSelector: '.eurovoc-heatmap-container',
  baseFilename: 'eurovoc-heatmap',
  exclusionAttributes: ['data-export-ignore'],
});

const timelineOptions = [
  { label: 'Today', value: TimelineOptions.TODAY },
  { label: 'Last 7 days', value: TimelineOptions.WEEK },
  { label: 'Last 30 days', value: TimelineOptions.MONTH },
];

const setDateRange = (filter: TimelineOptions): DateRange => {
  const endDate = new Date();
  let startDate: Date;

  switch (filter) {
    case TimelineOptions.TODAY:
      startDate = new Date();
      break;
    case TimelineOptions.WEEK:
      startDate = new Date(new Date().setDate(endDate.getDate() - 7));
      break;
    case TimelineOptions.MONTH:
      startDate = new Date(new Date().setDate(endDate.getDate() - 30));
      break;
    default:
      startDate = new Date();
  }

  return [startDate, endDate];
};

const dashboardStore = useDashboardStore();
const appStore = useAppStore();

const timelineFilter = ref<AaSelectOption<TimelineOptions>>(timelineOptions[2]);
const selectedDateRange = ref<DateRange>(setDateRange(timelineOptions[2].value));
const showTopicsDialog = ref(false);

const heatmapData = computed((): HeatmapDataItem[] => {
  return dashboardStore.eurovocData.map((item) => ({
    id: item.descriptor,
    label: item.descriptor,
    value: item.frequency,
  }));
});

const displayData = computed(() => {
  return heatmapData.value.slice(0, 12);
});

const valueRange = computed(() => {
  return {
    max: Math.max(...displayData.value.map((item) => item.value)),
    min: Math.min(...displayData.value.map((item) => item.value)),
  };
});

const exportOptions = [
  {
    label: 'Export widget as PNG',
    value: EXPORT_FORMAT.PNG,
  },
  {
    label: 'Export data as CSV',
    value: EXPORT_FORMAT.CSV,
  },
];

const fetchEurovocData = async (dateRange: DateRange) => {
  try {
    await dashboardStore.fetchEurovocOverview(
      dateRange,
      dashboardStore.currentJournalSeries || undefined
    );
  } catch (err: any) {
    console.error('Error fetching EuroVoc overview:', err);
  }
};

const handleTimelineChange = async (selectedOption: AaSelectModelValue) => {
  if (selectedOption) {
    const option = timelineOptions.find((opt) => opt.value === selectedOption.value);
    if (option) {
      timelineFilter.value = option;
      selectedDateRange.value = setDateRange(option.value);
      fetchEurovocData(selectedDateRange.value);
    }
  }
};

const handleBrowseAllTopics = () => {
  showTopicsDialog.value = true;
};

const handleExportToCSV = () => {
  try {
    const topics = dashboardStore.eurovocData;
    const filter = timelineFilter.value.label;
    const filenamePrefix = 'eurovoc-heatmap';

    // Sort topics by frequency (highest first)
    const sortedTopics = [...topics].sort((a, b) => b.frequency - a.frequency);

    // Prepare CSV data
    const headers = ['Rank', 'Eurovoc Topic', 'Frequency'];
    const csvRows = [
      headers.join(','), // Header row
      ...sortedTopics.map((topic, index) =>
        [
          index + 1,
          `"${topic.descriptor.replace(/"/g, '""')}"`, // Escape quotes in CSV
          topic.frequency,
        ].join(',')
      ),
    ];

    const csvContent = csvRows.join('\n');

    // Generate filename with timeline filter and timestamp
    const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    const timelineLabel = filter?.toLowerCase().replace(/\s+/g, '-') || 'all';
    const filename = `${filenamePrefix}-${timelineLabel}-${timestamp}`;

    downloadFile(csvContent, filename, {
      mimeType: 'text/csv;charset=utf-8;',
      fileExtension: 'csv',
    });
  } catch (error) {
    console.error('Error exporting to CSV:', error);
    throw error;
  }
};

const handleExport = (format: string) => {
  if (format === EXPORT_FORMAT.PNG) {
    handleWidgetExport(EXPORT_FORMAT.PNG);
  } else if (format === EXPORT_FORMAT.CSV) {
    handleExportToCSV();
  }
};

watch(
  () => dashboardStore.currentJournalSeries,
  () => {
    fetchEurovocData(selectedDateRange.value);
  }
);

watch(
  () => appStore.activeTab,
  async (newTab, oldTab) => {
    if (newTab === MonitoringTab.DASHBOARD && oldTab !== MonitoringTab.DASHBOARD) {
      await fetchEurovocData(selectedDateRange.value);
    }
  }
);

const initializeWidget = async () => {
  await fetchEurovocData(selectedDateRange.value);
};

onMounted(() => {
  initializeWidget();
});
</script>

<template>
  <div
    class="eurovoc-heatmap-container bg-core-bg-primary container flex w-full flex-col items-start gap-4 rounded-lg p-4"
  >
    <div class="flex w-full items-start justify-between">
      <div class="flex flex-col gap-1">
        <AaText class="text-core-content-secondary font-bold"> Eurovoc Topic Heatmap </AaText>
        <AaText class="text-core-content-tertiary text-sm">
          {{ `Displaying top ${displayData.length} topics with the highest activity` }}
        </AaText>
      </div>

      <div class="flex items-center gap-2">
        <AaButton
          size="medium"
          variant="text"
          @click="handleBrowseAllTopics"
          :disabled="dashboardStore.isLoadingEurovoc"
          v-if="heatmapData.length > 12"
          data-export-ignore
        >
          Browse all topics
        </AaButton>
        <AaSelect
          size="small"
          :options="timelineOptions"
          :model-value="timelineFilter"
          :disabled="dashboardStore.isLoadingEurovoc"
          @update:model-value="handleTimelineChange"
          data-export-ignore
        />
        <WidgetExportButton
          :export-options="exportOptions"
          @export="handleExport"
          :disabled="dashboardStore.isLoadingEurovoc"
          data-export-ignore
        />
      </div>
    </div>

    <div class="p-t-4 p-b-4 p-l-5 p-r-5 w-full">
      <HeatmapVisualization
        :data="heatmapData"
        :max-items="12"
        :loading="dashboardStore.isLoadingEurovoc"
      >
        <HeatmapGrid
          :is-empty="displayData.length === 0"
          empty-message="No Eurovoc topics found for the selected period."
        >
          <div class="grid grid-cols-3 gap-1.5">
            <HeatmapCell
              v-for="item in displayData"
              :key="item.id || item.label"
              :label="item.label"
              :value="item.value"
              :max-value="valueRange.max"
              :min-value="valueRange.min"
            />
          </div>
        </HeatmapGrid>
        <HeatmapLegend v-if="displayData.length > 0" class="m-t-4 flex items-start">
          <template #before>
            <AaText size="xs" class="m-r-3">Activity Level:</AaText>
          </template>
        </HeatmapLegend>
      </HeatmapVisualization>
    </div>

    <!-- EuroVoc Topics Dialog -->
    <EurovocTopicsDialog
      v-if="heatmapData.length > 12"
      :topics="dashboardStore.eurovocData"
      :timeline-filter="timelineFilter.label"
      :open="showTopicsDialog"
      :loading="dashboardStore.isLoadingEurovoc"
      :export-handler="handleExportToCSV"
      @update:open="showTopicsDialog = $event"
    />
  </div>
</template>

<style scoped>
.container {
  min-height: 350px;
}
</style>

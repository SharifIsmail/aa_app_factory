<script setup lang="ts">
import ClassificationComparison from './ClassificationComparison.vue';
import DetailedClassificationWidget from './DetailedClassificationWidget.vue';
import LegalActOverviewWidget from './LegalActOverviewWidget.vue';
import { useWidgetExport, EXPORT_FORMAT } from '@/@core/composables/useWidgetExport';
import { useDashboardStore } from '@/modules/monitoring/stores/dashboardStore';
import {
  type DateRange,
  type AIClassificationCounts,
  type HumanDecisionCounts,
} from '@/modules/monitoring/types';
import {
  AaSelect,
  AaText,
  AaIconButton,
  type AaSelectOption,
} from '@aleph-alpha/ds-components-vue';
import { ref, onMounted, watch, computed } from 'vue';

const dashboardStore = useDashboardStore();
const { handleExport } = useWidgetExport({
  containerSelector: '.dashboard-overview-container',
  baseFilename: 'dashboard-overview',
  exclusionAttributes: ['data-export-ignore'],
});

enum TimelineOptions {
  TODAY = 'today',
  WEEK = 'week',
  MONTH = 'month',
}
const timelineOptions = [
  { label: 'Today', value: TimelineOptions.TODAY },
  { label: 'Last 7 days', value: TimelineOptions.WEEK },
  { label: 'Last 30 days', value: TimelineOptions.MONTH },
];

const selectedTimelineOption = ref<AaSelectOption<TimelineOptions>>(timelineOptions[0]);
const timelineFilter = computed(() => selectedTimelineOption.value.value);
const totalLegalActs = ref<number>(0);
const totalEvaluations = ref<number>(0);
const dateRange = ref<DateRange>([new Date(), new Date()]);
const aiClassification = ref<AIClassificationCounts>({});
const humanClassification = ref<HumanDecisionCounts>({});
const recallValue = ref<number>(0);
const setDateRange = (timelineFilter: TimelineOptions) => {
  switch (timelineFilter) {
    case TimelineOptions.TODAY: {
      const today = new Date();
      return [today, today];
    }
    case TimelineOptions.WEEK: {
      const week = new Date(new Date().setDate(new Date().getDate() - 7));
      return [week, new Date()];
    }
    case TimelineOptions.MONTH: {
      const month = new Date(new Date().setDate(new Date().getDate() - 30));
      return [month, new Date()];
    }
  }
};
const handleTimelineChange = async (value: TimelineOptions) => {
  dateRange.value = setDateRange(value) as DateRange;
  const response = await dashboardStore.fetchLegalActOverview(
    dateRange.value,
    dashboardStore.currentJournalSeries || undefined
  );
  totalLegalActs.value = response.total_acts || 0;
  totalEvaluations.value = response.total_evaluations || 0;
  aiClassification.value = response.ai_classification || {};
  humanClassification.value = response.human_decision || {};
};

const fetchRecallValue = async () => {
  const response = await dashboardStore.fetchLegalActOverview();
  recallValue.value = response.metrics?.recall || 0;
};

onMounted(() => {
  handleTimelineChange(TimelineOptions.TODAY);
  fetchRecallValue();
});

watch(
  () => dashboardStore.currentJournalSeries,
  () => {
    handleTimelineChange(timelineFilter.value);
  }
);
</script>

<template>
  <div>
    <!-- Dashboard Content -->
    <div class="m-t-4 flex gap-5">
      <div
        class="dashboard-overview-container bg-core-bg-primary flex flex-col items-start gap-2 rounded-lg p-4"
      >
        <!-- Filters -->
        <div class="flex w-full items-center justify-between">
          <AaText class="text-core-content-secondary text-base font-bold">Overview</AaText>
          <div class="flex items-center gap-2">
            <AaSelect
              :options="timelineOptions"
              variant="text"
              :model-value="selectedTimelineOption"
              @update:model-value="
                (option) => {
                  if (option) {
                    selectedTimelineOption = option as AaSelectOption<TimelineOptions>;
                    handleTimelineChange(selectedTimelineOption.value);
                  }
                }
              "
              data-export-ignore
            />
            <AaIconButton
              variant="ghost"
              icon="i-material-symbols-download"
              size="small"
              label="Export as PNG"
              tooltip-text="Export as PNG"
              @click="handleExport(EXPORT_FORMAT.PNG)"
              data-export-ignore
            />
          </div>
        </div>
        <!-- Top Row - Interactive Timeline -->
        <div class="flex">
          <LegalActOverviewWidget
            :total-legal-acts="totalLegalActs"
            :date-range="dateRange"
            :total-evaluations="totalEvaluations"
          />
          <DetailedClassificationWidget
            :total-legal-acts="totalLegalActs"
            :date-range="dateRange"
            :ai-classification="aiClassification"
            :human-classification="humanClassification"
          />
        </div>
      </div>
      <ClassificationComparison :recall-value="recallValue" />
    </div>
  </div>
</template>

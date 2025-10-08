<script setup lang="ts">
import { useWidgetExport, EXPORT_FORMAT } from '@/@core/composables/useWidgetExport';
import { useAppStore } from '@/modules/monitoring/stores/appStore';
import { useDashboardStore } from '@/modules/monitoring/stores/dashboardStore';
import { type DateRange, MonitoringTab } from '@/modules/monitoring/types';
import {
  AaText,
  AaSelect,
  AaIconButton,
  type AaSelectModelValue,
} from '@aleph-alpha/ds-components-vue';
import { ref, computed, watch, onMounted } from 'vue';

enum TimelineOptions {
  TODAY = 'today',
  WEEK = 'week',
  MONTH = 'month',
}

const { handleExport } = useWidgetExport({
  containerSelector: '.affected-departments-container',
  baseFilename: 'affected-departments',
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

const timelineFilter = ref<AaSelectModelValue<TimelineOptions>>(timelineOptions[2]);
const selectedDateRange = ref<DateRange>(setDateRange(timelineOptions[2].value));

const departmentsData = computed(() => {
  const departments = dashboardStore.departmentsData.slice(0, 10);
  const maxValue = Math.max(...departments.map((d) => d.relevant_acts));

  return departments.map((dept) => ({
    department: dept.department,
    count: dept.relevant_acts,
    percentage: maxValue > 0 ? (dept.relevant_acts / maxValue) * 100 : 0,
  }));
});

const fetchDepartmentsData = async (dateRange: DateRange) => {
  try {
    const range = dateRange;
    await dashboardStore.fetchDepartmentsOverview(
      range,
      dashboardStore.currentJournalSeries || undefined
    );
  } catch (err: any) {
    console.error('Error fetching departments overview:', err);
  }
};

const handleTimelineChange = async (selectedOption: AaSelectModelValue) => {
  if (selectedOption) {
    const option = timelineOptions.find((opt) => opt.value === selectedOption.value);
    if (option) {
      timelineFilter.value = option;
      selectedDateRange.value = setDateRange(option.value);
      fetchDepartmentsData(selectedDateRange.value);
    }
  }
};

watch(
  () => dashboardStore.currentJournalSeries,
  () => {
    fetchDepartmentsData(selectedDateRange.value);
  }
);

watch(
  () => appStore.activeTab,
  async (newTab, oldTab) => {
    if (newTab === MonitoringTab.DASHBOARD && oldTab !== MonitoringTab.DASHBOARD) {
      await fetchDepartmentsData(selectedDateRange.value);
    }
  }
);

const initializeWidget = async () => {
  await fetchDepartmentsData(selectedDateRange.value);
};

onMounted(() => {
  initializeWidget();
});
</script>

<template>
  <div
    class="affected-departments-container bg-core-bg-primary container flex w-full flex-col items-start gap-6 rounded-lg p-4"
  >
    <!-- Header with controls -->
    <div class="flex w-full items-center justify-between">
      <div class="flex flex-col gap-1">
        <AaText class="text-core-content-secondary font-bold">
          Affected departments ({{ dashboardStore.totalRelevantActs }} acts)
        </AaText>
        <AaText class="text-core-content-tertiary text-sm">
          Which departments got affected the most
        </AaText>
      </div>

      <!-- Date range controls -->
      <div class="flex items-center gap-2">
        <AaSelect
          :options="timelineOptions"
          :model-value="timelineFilter"
          :disabled="dashboardStore.isLoadingDepartments"
          data-export-ignore
          @update:model-value="handleTimelineChange"
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

    <!-- Content -->
    <div class="p-t-4 p-b-4 p-l-5 p-r-5 w-full">
      <!-- Error State -->
      <div v-if="dashboardStore.error" class="flex h-32 items-center justify-center">
        <AaText class="text-core-content-secondary text-sm">
          Failed to load departments data. Please try again.
        </AaText>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="dashboardStore.departmentsData.length === 0"
        class="flex h-32 items-center justify-center"
      >
        <AaText class="text-core-content-secondary text-sm">
          No departments with relevant legal acts found for the selected period.
        </AaText>
      </div>

      <!-- Custom Bar Visualization -->
      <div v-else class="w-8/10 space-y-4">
        <div
          v-for="dept in departmentsData"
          :key="dept.department"
          class="flex items-center gap-10"
        >
          <div class="w-32 flex-shrink-0">
            <AaText class="text-core-content-tertiary truncate text-sm leading-5">
              {{ dept.department }}
            </AaText>
          </div>
          <div class="flex flex-1 items-center gap-3">
            <div
              class="bar h-full bg-purple-500 transition-all duration-500 ease-out"
              :style="{ width: `${dept.percentage}%` }"
            ></div>

            <AaText class="text-core-content-secondary text-sm font-semibold">
              {{ dept.count }}
            </AaText>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  min-height: 300px;
}

.bar {
  height: 20px;
  background-color: #555cf9;
}
</style>

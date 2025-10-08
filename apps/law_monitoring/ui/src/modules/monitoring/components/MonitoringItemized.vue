<script setup lang="ts">
import MonitoringDisplay from './MonitoringDisplay.vue';
import MonitoringFilters from './MonitoringFilters.vue';
import { DATE_RANGE_RESET } from '@/modules/monitoring/constants';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore.ts';
import { DisplayMode, useLawDisplayStore } from '@/modules/monitoring/stores/lawDisplayStore.ts';
import { type DateRange } from '@/modules/monitoring/types';
import { ref, onMounted, nextTick, onUnmounted } from 'vue';

interface Props {
  height: number;
}

const props = defineProps<Props>();

const lawDisplayStore = useLawDisplayStore();
const lawCoordinatorStore = useLawCoordinatorStore();

// Height calculation refs
const monitoringFiltersRef = ref<HTMLElement>();
const monitoringDisplayHeight = ref('100%');
let resizeObserver: ResizeObserver | null = null;

const isDateAvailable = (d: Date) =>
  lawCoordinatorStore.getAvailableDates.includes(d.toISOString().split('T')[0]);

const checkDateRangeAvailability = (startDate: Date, endDate: Date): boolean => {
  const currentDate = new Date(startDate);
  while (currentDate <= endDate) {
    if (isDateAvailable(currentDate)) {
      return true;
    }
    currentDate.setDate(currentDate.getDate() + 1);
  }
  return false;
};

const handleDateRangeChange = async (dateRange: DateRange | null | typeof DATE_RANGE_RESET) => {
  // Allow null to clear selection
  lawDisplayStore.setDateSelectionMessage('');
  lawDisplayStore.setSelectedDateRange(undefined);

  if (dateRange === DATE_RANGE_RESET) {
    return;
  }

  if (!dateRange) {
    // Stay in current view and load all laws when date range is cleared
    lawDisplayStore.displayMode = DisplayMode.DEFAULT;
    await lawCoordinatorStore.loadDefaultLaws();
    return;
  }

  const [startDate, endDate] = dateRange;

  // Check if any dates in the range have available data
  const hasAvailableData = checkDateRangeAvailability(startDate, endDate);

  if (!hasAvailableData) {
    lawDisplayStore.setDateSelectionMessage(`No legal acts available for the selected date range.`);
    return;
  }

  lawDisplayStore.setSelectedDateRange(dateRange);
  await lawCoordinatorStore.fetchLawsByDateRange(dateRange);
};

const updateHeights = async () => {
  await nextTick();

  if (monitoringFiltersRef.value) {
    const filtersHeight = monitoringFiltersRef.value.offsetHeight;
    const containerHeight = props.height || 0;
    const availableHeight = containerHeight - filtersHeight;

    if (filtersHeight > 0 && availableHeight > 0) {
      monitoringDisplayHeight.value = `${availableHeight}px`;
    }
  }
};

onMounted(async () => {
  await updateHeights();

  if (!lawDisplayStore.selectedDateRange) {
    await lawCoordinatorStore.loadDefaultLaws();
  }

  if (monitoringFiltersRef.value) {
    resizeObserver = new ResizeObserver(() => {
      updateHeights();
    });
    resizeObserver.observe(monitoringFiltersRef.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});
</script>

<template>
  <div class="flex flex-1 flex-col overflow-hidden">
    <!-- Filters -->
    <div ref="monitoringFiltersRef">
      <MonitoringFilters
        :selected-date-range="lawDisplayStore.selectedDateRange"
        :date-selection-message="lawDisplayStore.dateSelectionMessage"
        @date-range-change="handleDateRangeChange"
      />
    </div>

    <!-- List View -->
    <div
      class="flex flex-col items-center gap-4 self-stretch overflow-y-auto"
      :style="{ height: monitoringDisplayHeight }"
    >
      <MonitoringDisplay />
    </div>
  </div>
</template>

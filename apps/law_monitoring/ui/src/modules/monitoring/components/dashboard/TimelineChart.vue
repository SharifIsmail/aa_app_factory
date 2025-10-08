<script setup lang="ts">
import { useAppStore } from '@/modules/monitoring/stores/appStore';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore';
import { useLawDisplayStore } from '@/modules/monitoring/stores/lawDisplayStore';
import {
  type LegalActTimeline,
  Category,
  type DateRange,
  MonitoringTab,
} from '@/modules/monitoring/types';
import {
  LineChart,
  BarChart,
  type ChartData,
  type ChartEvent,
  type ActiveElement,
  ChartType,
} from '@app-factory/shared-frontend/components';
import { computed, type PropType } from 'vue';

const props = defineProps({
  timelineData: {
    type: Array as PropType<LegalActTimeline[]>,
    required: true,
  },
  chartType: {
    type: String as PropType<ChartType>,
    default: ChartType.LINE,
  },
  dateRangeDisplay: {
    type: String,
    default: 'Timeline',
  },
});

const lawDisplayStore = useLawDisplayStore();
const appStore = useAppStore();
const lawCoordinatorStore = useLawCoordinatorStore();

const chartData = computed((): ChartData<ChartType.LINE> | ChartData<ChartType.BAR> => {
  const dates = props.timelineData.map((item) =>
    new Date(item.date || '').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  );
  const totalCounts = props.timelineData.map((item) => item.legal_acts || 0);
  const awaitingDecisionCounts = props.timelineData.map(
    (item) => item.human_decision?.awaiting_decision || 0
  );
  const relevantCounts = props.timelineData.map((item) => item.human_decision?.relevant || 0);
  const notRelevantCounts = props.timelineData.map(
    (item) => item.human_decision?.not_relevant || 0
  );

  const barDatasets = [
    {
      label: 'Awaiting Human Review',
      data: awaitingDecisionCounts,
      borderColor: '#FCDC3C',
      backgroundColor: '#FCDC3C',
      yAxisID: 'y',
      borderWidth: 1,
      stack: 'stack1',
    },
    {
      label: 'Reviewed',
      data: relevantCounts.map((count, index) => count + notRelevantCounts[index]),
      borderColor: '#555CF9',
      backgroundColor: '#555CF9',
      yAxisID: 'y',
      borderWidth: 1,
      stack: 'stack1',
    },
  ];

  const lineDatasets = [
    {
      label: 'Total legal acts',
      data: totalCounts,
      borderColor: '#854D0E',
      backgroundColor: '#854D0E',
      tension: 0.3,
      borderWidth: 1,
      yAxisID: 'y',
    },
    {
      label: 'Relevant legal acts',
      data: relevantCounts,
      borderColor: '#4841F2',
      backgroundColor: '#4841F2',
      yAxisID: 'y1',
      tension: 0.3,
      borderWidth: 1,
    },
  ];

  return {
    labels: dates,
    datasets: props.chartType === ChartType.LINE ? lineDatasets : barDatasets,
  };
});

const chartOptions = computed(() => {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          boxWidth: 12,
          boxHeight: 12,
          padding: 8,
          usePointStyle: false,
          font: {
            size: 11,
          },
        },
      },
      tooltip: {
        mode: props.chartType === ChartType.BAR ? ('index' as const) : ('point' as const),
        intersect: false,
        callbacks: {
          title: (context: any) => {
            return `Date: ${context[0].label}`;
          },
          label: (context: any) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return `${label}: ${value} acts`;
          },
        },
      },
    },
    scales: {
      x: {
        title: {
          text: `Timeline`,
        },
      },
      y: {
        title: {
          text: 'Total Legal Acts',
        },
      },
      ...(props.chartType === ChartType.LINE && {
        y1: {
          type: 'linear' as const,
          display: true,
          position: 'right' as const,
          title: {
            display: true,
            text: 'Relevant Legal Acts',
            font: {
              size: 12,
              weight: 'bold' as const,
            },
          },
          ticks: {
            font: {
              size: 11,
            },
            stepSize: 1,
          },
          grid: {
            drawOnChartArea: false,
          },
        },
      }),
    },
    ...(props.chartType === ChartType.BAR && {
      interaction: {
        mode: 'point' as const,
        intersect: true,
      },
    }),
  };

  return baseOptions;
});

const handleChartClick = (event: ChartEvent, elements: ActiveElement[]) => {
  if (elements.length > 0) {
    lawDisplayStore.isInitialFilterApplied = false;
    const element = elements[0];
    const datasetIndex = element.datasetIndex;
    const index = element.index;

    const timelineItem = props.timelineData[index];
    const clickedSegment = chartData.value.datasets[datasetIndex].label ?? '';

    navigateToListView(timelineItem.date, clickedSegment);
  }
};

const handleChartHover = (event: ChartEvent, elements: ActiveElement[]) => {
  if (event.native?.target) {
    (event.native.target as HTMLElement).style.cursor = elements.length > 0 ? 'pointer' : 'default';
  }
};

const navigateToListView = async (date?: string, segment?: string) => {
  if (!date || !segment) return;

  const datePart = date.split('T')[0];
  const filterDate = new Date(datePart);
  const dateRange: DateRange = [filterDate, filterDate];

  lawDisplayStore.setSelectedDateRange(dateRange);
  lawDisplayStore.setAiClassificationFilter('ALL');

  switch (segment) {
    case 'Marked Relevant':
      lawDisplayStore.setCategoryFilter(Category.RELEVANT);
      break;
    case 'Marked Not Relevant':
      lawDisplayStore.setCategoryFilter(Category.NOT_RELEVANT);
      break;
    case 'Awaiting Human Review':
      lawDisplayStore.setCategoryFilter(Category.OPEN);
      break;
    default:
      lawDisplayStore.setCategoryFilter('ALL');
  }

  lawCoordinatorStore.fetchLawsByDateRange(dateRange);
  appStore.setActiveTab(MonitoringTab.LIST);
};
</script>

<template>
  <LineChart
    class="h-full"
    v-if="props.chartType === ChartType.LINE"
    :data="chartData as ChartData<ChartType.LINE>"
    :options="chartOptions"
  />
  <BarChart
    class="h-full"
    v-if="props.chartType === ChartType.BAR"
    :data="chartData as ChartData<ChartType.BAR>"
    :options="chartOptions"
    @click="handleChartClick"
    @hover="handleChartHover"
  />
</template>

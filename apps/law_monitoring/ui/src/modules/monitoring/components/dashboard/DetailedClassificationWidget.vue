<script setup lang="ts">
import { useAppStore } from '@/modules/monitoring/stores/appStore';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore';
import { useLawDisplayStore } from '@/modules/monitoring/stores/lawDisplayStore';
import {
  AiClassification,
  Category,
  type DateRange,
  MonitoringTab,
  type AIClassificationCounts,
  type HumanDecisionCounts,
} from '@/modules/monitoring/types';
import { AaText } from '@aleph-alpha/ds-components-vue';
import {
  DoughnutChart,
  type ChartEvent,
  type ActiveElement,
  type ChartJS,
} from '@app-factory/shared-frontend/components';
import { computed } from 'vue';

const props = defineProps<{
  totalLegalActs: number;
  dateRange: DateRange;
  aiClassification: AIClassificationCounts;
  humanClassification: HumanDecisionCounts;
}>();

const lawDisplayStore = useLawDisplayStore();
const lawCoordinatorStore = useLawCoordinatorStore();
const appStore = useAppStore();
const aiClassificationChartData = computed(() => {
  const likelyRelevant = props.aiClassification.likely_relevant || 0;
  const likelyIrrelevant = props.aiClassification.likely_not_relevant || 0;
  return {
    labels: [`(${likelyIrrelevant}) Likely Not Relevant `, `(${likelyRelevant}) Likely Relevant `],
    datasets: [
      {
        data: [likelyIrrelevant, likelyRelevant],
        borderColor: '#FBFBFD',
        backgroundColor: ['#FE8C8C', '#555CF9'],
      },
    ],
  };
});

const humanClassificationChartData = computed(() => {
  const relevant = props.humanClassification.relevant || 0;
  const open = props.humanClassification.awaiting_decision || 0;
  const notRelevant = props.humanClassification.not_relevant || 0;
  return {
    labels: [`(${notRelevant}) Not Relevant`, `(${open}) No Decision`, `(${relevant}) Relevant`],
    datasets: [
      {
        data: [notRelevant, open, relevant],
        borderColor: '#FBFBFD',
        backgroundColor: ['#FE8C8C', '#FCDC3C', '#555CF9'],
      },
    ],
  };
});

const doughnutChartStyles = computed<any>(() => {
  return {
    height: '80px',
    width: '300px',
    margin: '0',
    padding: '0',
  };
});

const doughnutChartOptions = computed<any>(() => {
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
      legend: {
        display: true,
        position: 'right',
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
        callbacks: {
          title: (tooltipItems: any) => {
            const label = tooltipItems[0]?.label || '';
            // Extracts text after the count, e.g., "(15) Likely Relevant " -> "Likely Relevant"
            return label.substring(label.indexOf(')') + 1).trim();
          },
        },
      },
    },
  };
});

const handleChartClick = (event: ChartEvent, elements: ActiveElement[], chart: ChartJS) => {
  if (elements.length > 0) {
    lawDisplayStore.isInitialFilterApplied = false;
    const dataIndex = elements[0].index;
    let label = chart.data.labels?.[dataIndex] as string;
    label = label.substring(label.indexOf(')') + 1).trim();
    filterLaws(label);
  }
};

const handleChartHover = (event: ChartEvent, elements: ActiveElement[]) => {
  if (event.native?.target) {
    (event.native.target as HTMLElement).style.cursor = elements.length > 0 ? 'pointer' : 'default';
  }
};

const filterLaws = (label: string) => {
  lawDisplayStore.setSelectedDateRange(props.dateRange || undefined);
  appStore.setActiveTab(MonitoringTab.LIST);
  switch (label) {
    case 'Likely Relevant':
      lawDisplayStore.setCategoryFilter('ALL');
      lawDisplayStore.setAiClassificationFilter(AiClassification.LIKELY_RELEVANT);
      break;
    case 'Likely Not Relevant':
      lawDisplayStore.setCategoryFilter('ALL');
      lawDisplayStore.setAiClassificationFilter(AiClassification.LIKELY_IRRELEVANT);
      break;
    case 'Awaiting Decision':
      lawDisplayStore.setAiClassificationFilter('ALL');
      lawDisplayStore.setCategoryFilter(Category.OPEN);
      break;
    case 'Relevant':
      lawDisplayStore.setAiClassificationFilter('ALL');
      lawDisplayStore.setCategoryFilter(Category.RELEVANT);
      break;
    case 'Not Relevant':
      lawDisplayStore.setAiClassificationFilter('ALL');
      lawDisplayStore.setCategoryFilter(Category.NOT_RELEVANT);
      break;
  }

  lawCoordinatorStore.fetchLawsByDateRange(props.dateRange);
};
</script>

<template>
  <div
    class="border-core-border-default bg-core-bg-primary p-t-3 p-r-4 p-b-3 p-l-4 flex flex-col rounded-r-lg border"
  >
    <div class="flex flex-col gap-1 p-1">
      <AaText class="text-core-content-secondary text-base font-bold">
        Detailed classification ({{ totalLegalActs }} total acts)
      </AaText>
      <AaText class="text-core-content-tertiary text-sm">
        Breakdown of AI classifications versus human classifications
      </AaText>
    </div>

    <div class="flex flex-row p-5">
      <div
        class="flex flex-col gap-2"
        v-if="props.aiClassification.likely_relevant || props.aiClassification.likely_not_relevant"
      >
        <AaText class="text-core-content-tertiary text-xs font-bold"> AI Classification </AaText>
        <DoughnutChart
          :data="aiClassificationChartData"
          :style="doughnutChartStyles"
          :options="doughnutChartOptions"
          @click="handleChartClick"
          @hover="handleChartHover"
        />
      </div>
      <div
        class="flex flex-col gap-2"
        v-if="
          props.humanClassification.relevant ||
          props.humanClassification.awaiting_decision ||
          props.humanClassification.not_relevant
        "
      >
        <AaText class="text-core-content-tertiary text-xs font-bold"> Human Classification </AaText>
        <DoughnutChart
          :data="humanClassificationChartData"
          :style="doughnutChartStyles"
          :options="doughnutChartOptions"
          @click="handleChartClick"
          @hover="handleChartHover"
        />
      </div>
      <div v-else class="flex h-full items-center justify-center p-6">
        <div class="text-center">
          <AaText class="text-core-content-secondary mb-2 text-base"
            >No classification data available for this date range</AaText
          >
          <AaText class="text-core-content-secondary text-sm opacity-75"
            >Please try refreshing or change your date range</AaText
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DEFAULT_COLORS, DEFAULT_FONT_FAMILY } from './types';
import { ChartType } from './types';
import {
  Chart as ChartJS,
  ArcElement,
  DoughnutController,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
  type ChartEvent,
  type ActiveElement,
} from 'chart.js';
import merge from 'lodash/merge';
import { computed, type CSSProperties } from 'vue';
import { Doughnut } from 'vue-chartjs';

// Register Chart.js components
ChartJS.register(ArcElement, DoughnutController, Title, Tooltip, Legend);

interface Props {
  /** Chart.js data object */
  data: ChartData<ChartType.DOUGHNUT>;
  /** Chart.js options object */
  options?: ChartOptions<ChartType.DOUGHNUT>;
  /** Container style as CSSProperties */
  style?: CSSProperties;
  /** Custom CSS classes */
  class?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  chartReady: [chart: ChartJS];
  click: [event: ChartEvent, elements: ActiveElement[], chart: ChartJS];
  hover: [event: ChartEvent, elements: ActiveElement[], chart: ChartJS];
}>();

// Container styling - merge user styles with any defaults
const containerStyle = computed((): CSSProperties => {
  return {
    ...props.style,
  };
});

// Apply default colors if no colors are set
const data = computed(() => {
  const processedDatasets = props.data.datasets.map((dataset) => {
    if (dataset.backgroundColor) {
      return dataset;
    }

    // For doughnut charts, we need colors for each data point
    const colors = DEFAULT_COLORS.slice(0, props.data.labels?.length || DEFAULT_COLORS.length);

    return {
      ...dataset,
      backgroundColor: colors,
      borderColor: colors.map((color) =>
        color.includes('rgba') ? color : color.replace('rgb', 'rgba').replace(')', ', 1)')
      ),
      borderWidth: 2,
    };
  });

  return {
    ...props.data,
    datasets: processedDatasets,
  };
});

// Handle chart click events
const handleChartClick = (event: ChartEvent, elements: ActiveElement[], chart: ChartJS) => {
  emit('click', event, elements, chart);
};

const handleChartHover = (event: ChartEvent, elements: ActiveElement[], chart: ChartJS) => {
  emit('hover', event, elements, chart);
};

const mergedOptions = computed(() => {
  const defaultOptions: ChartOptions<ChartType.DOUGHNUT> = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: handleChartClick,
    onHover: handleChartHover,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          font: {
            family: DEFAULT_FONT_FAMILY,
          },
          padding: 20,
          usePointStyle: true,
        },
      },
      tooltip: {
        titleFont: {
          family: DEFAULT_FONT_FAMILY,
        },
        bodyFont: {
          family: DEFAULT_FONT_FAMILY,
        },
      },
    },
  };

  const userOptions = props.options || {};

  const mergedClickHandler = userOptions.onClick
    ? (event: ChartEvent, elements: ActiveElement[], chart: ChartJS) => {
        handleChartClick(event, elements, chart);
        userOptions.onClick!(event, elements, chart);
      }
    : handleChartClick;

  const mergedHoverHandler = userOptions.onHover
    ? (event: ChartEvent, elements: ActiveElement[], chart: ChartJS) => {
        handleChartHover(event, elements, chart);
        userOptions.onHover!(event, elements, chart);
      }
    : handleChartHover;

  const merged = merge({}, defaultOptions, userOptions);
  merged.onClick = mergedClickHandler;
  merged.onHover = mergedHoverHandler;
  return merged;
});
</script>

<template>
  <div :class="props.class" :style="containerStyle">
    <Doughnut :data="data" :options="mergedOptions" @chart:render="$emit('chartReady', $event)" />
  </div>
</template>

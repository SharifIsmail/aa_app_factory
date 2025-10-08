<script setup lang="ts">
import { commonChartOptions } from './constants';
import { DEFAULT_COLORS } from './types';
import { ChartType } from './types';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
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
import { Bar } from 'vue-chartjs';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, BarController, Title, Tooltip, Legend);

interface Props {
  /** Chart.js data object */
  data: ChartData<ChartType.BAR>;
  /** Chart.js options object */
  options?: ChartOptions<ChartType.BAR>;
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

const data = computed(() => {
  const processedDatasets = props.data.datasets.map((dataset, index) => {
    if (dataset.backgroundColor || dataset.borderColor) {
      return dataset;
    }

    const colorIndex = index % DEFAULT_COLORS.length;
    const color = DEFAULT_COLORS[colorIndex];

    return {
      ...dataset,
      backgroundColor: color.replace(')', ', 0.8)').replace('rgb', 'rgba'),
      borderColor: color,
      borderWidth: 1,
      borderRadius: 4,
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
  const defaultOptions: ChartOptions<ChartType.BAR> = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: handleChartClick,
    onHover: handleChartHover,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    ...commonChartOptions,
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
    <Bar :data="data" :options="mergedOptions" @chart:render="$emit('chartReady', $event)" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  label: string;
  value: number;
  maxValue: number;
  minValue?: number;
  onClick?: () => void;
}

const props = withDefaults(defineProps<Props>(), {
  minValue: 0,
  onClick: undefined,
});

// Calculate intensity (0-1) for color mapping
const intensity = computed(() => {
  if (props.maxValue === props.minValue) return 0;
  return (props.value - props.minValue) / (props.maxValue - props.minValue);
});

// Color schemes with different intensities
const colorClasses = computed(() => {
  const baseClasses = 'transition-all duration-200 ease-in-out';
  const hoverClasses = props.onClick ? 'hover:scale-105 hover:shadow-md cursor-pointer' : '';
  const intensityLevel = Math.ceil(intensity.value * 5);
  const colorClass = `heatmap-level-${intensityLevel}`;

  return `${baseClasses} ${hoverClasses} ${colorClass}`;
});

const handleClick = () => {
  if (props.onClick) {
    props.onClick();
  }
};
</script>

<template>
  <div
    :class="['flex flex-col items-center justify-center rounded p-1 h-12', colorClasses]"
    @click="handleClick"
  >
    <span class="truncate w-full text-center text-xs">
      {{ label }}
    </span>

    <span class="text-xs">
      {{ value }}
    </span>
  </div>
</template>

<style scoped>
.heatmap-level-0 {
  background-color: #d0daff;
  color: #104067;
}

.heatmap-level-1 {
  background-color: #b2bfff;
  color: #104067;
}

.heatmap-level-2 {
  background-color: #9397fe;
  color: white;
}

.heatmap-level-3,
.heatmap-level-4 {
  background-color: #4841f2;
  color: white;
}

.heatmap-level-5 {
  background-color: #3421c7;
  color: white;
}
</style>

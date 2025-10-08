<script setup lang="ts">
import { computed, provide } from 'vue';

export interface HeatmapDataItem {
  label: string;
  value: number;
  id?: string;
}

interface Props {
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

provide(
  'heatmapLoading',
  computed(() => props.loading)
);
</script>

<template>
  <div class="w-full">
    <slot />
  </div>
</template>

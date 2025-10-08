<script setup lang="ts">
import { AaText } from '@aleph-alpha/ds-components-vue';

interface Props {
  lowLabel?: string;
  highLabel?: string;
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  lowLabel: 'Low',
  highLabel: 'High',
  class: '',
});
</script>

<template>
  <div :class="props.class">
    <slot name="before" />
    <div>
      <div class="flex items-center justify-center gap-2">
        <div class="flex gap-1">
          <div
            v-for="level in 5"
            :key="level"
            class="w-3 h-3 rounded-sm legend-level"
            :class="`legend-level-${level}`"
          />
        </div>
      </div>
      <div class="flex items-center justify-between">
        <AaText size="xs" class="text-core-content-tertiary">{{ props.lowLabel }}</AaText>
        <AaText size="xs" class="text-core-content-tertiary">{{ props.highLabel }}</AaText>
      </div>
    </div>

    <slot name="after" />
  </div>
</template>

<style scoped>
.legend-level-1 {
  background-color: #d0daff;
}

.legend-level-2 {
  background-color: #b2bfff;
}

.legend-level-3 {
  background-color: #9397fe;
}

.legend-level-4 {
  background-color: #4841f2;
}

.legend-level-5 {
  background-color: #3421c7;
}
</style>

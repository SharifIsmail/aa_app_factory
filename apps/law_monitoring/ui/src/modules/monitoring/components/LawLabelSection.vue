<script setup lang="ts">
import { AaText } from '@aleph-alpha/ds-components-vue';

defineProps<{
  title: string;
  label: string;
  colorClass: string;
}>();
</script>

<template>
  <div v-if="label">
    <AaText size="base" weight="bold" class="mb-2">{{ title }}</AaText>
    <div class="flex items-center gap-2">
      <span :class="['inline-block rounded-full px-3 py-1 text-xs font-medium', colorClass]">
        {{ label }}
      </span>
    </div>
  </div>
</template>

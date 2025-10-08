<script setup lang="ts">
interface Props {
  emptyMessage?: string;
  isEmpty?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  emptyMessage: 'No data available',
  isEmpty: false,
});
</script>

<template>
  <div v-if="props.isEmpty" class="flex items-center justify-center min-h-[200px]">
    <AaText size="sm" class="text-core-content-secondary">
      {{ props.emptyMessage }}
    </AaText>
  </div>

  <div v-else class="w-full">
    <slot />
  </div>
</template>

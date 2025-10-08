<script setup lang="ts">
interface Props {
  isLast?: boolean;
  bulletClass?: string;
}

withDefaults(defineProps<Props>(), {
  isLast: false,
  bulletClass: 'bg-core-border-default',
});
</script>

<template>
  <div class="timeline-item relative mb-4" :class="{ 'timeline-item-last': isLast }">
    <span
      class="absolute -left-6 top-0 mt-1.5 inline-flex size-2 rounded-full"
      :class="bulletClass"
    ></span>
    <div class="ml-2">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.timeline-item::before {
  content: '';
  position: absolute;
  left: -1.25rem;
  top: 0.75rem;
  bottom: -1.5rem;
  width: 1px;
  background-color: #dbdbe9;
}

/* Remove timeline line from last item */
.timeline-item-last::before {
  display: none;
}
</style>

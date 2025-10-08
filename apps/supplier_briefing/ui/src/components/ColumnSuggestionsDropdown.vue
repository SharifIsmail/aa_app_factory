<script setup lang="ts">
defineProps<{
  suggestions: string[];
  isOpen: boolean;
  highlightedIndex: number;
  position: { left: number; top: number };
}>();

const emit = defineEmits<{
  (e: 'select-suggestion', suggestion: string): void;
  (e: 'close-dropdown'): void;
  (e: 'highlight-index-change', index: number): void;
}>();

const selectSuggestion = (suggestion: string) => {
  emit('select-suggestion', suggestion);
};

const handleMouseMove = (index: number) => {
  emit('highlight-index-change', index);
};
</script>

<template>
  <div
    v-show="isOpen"
    class="w-100 absolute z-10"
    :style="{ left: position.left + 'px', top: position.top + 'px' }"
  >
    <ul class="bg-core-bg-primary border-core-border-contrast rounded border p-2 shadow">
      <li
        v-for="(suggestion, idx) in suggestions"
        :key="suggestion + idx"
        :class="[
          'rounded-1 text-core-content-secondary hover:text-core-content-primary hover:bg-selected-brand cursor-pointer px-3 py-2',
          idx === highlightedIndex ? 'bg-brand-bg-brand-soft text-core-content-primary' : '',
        ]"
        @mousedown.prevent
        @click="selectSuggestion(suggestion)"
        @mousemove="handleMouseMove(idx)"
      >
        {{ suggestion }}
      </li>
    </ul>
  </div>
</template>

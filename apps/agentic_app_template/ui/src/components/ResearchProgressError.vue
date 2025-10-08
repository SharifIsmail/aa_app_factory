<script setup lang="ts">
import { AaButton } from '@aleph-alpha/ds-components-vue';

defineProps<{
  error: { message: string; details?: any } | null;
}>();

const emit = defineEmits<{
  (e: 'restart'): void;
}>();

const handleRestart = () => {
  emit('restart');
};
</script>

<template>
  <div class="flex flex-col">
    <div class="mb-4 flex flex-col items-center rounded-lg border border-blue-100 bg-blue-50 p-6">
      <span class="success-icon i-material-symbols-error bg-semantic-bg-error mb-6 text-6xl" />
      <h3 class="mb-2 text-lg font-medium text-gray-800">We apologize for the interruption.</h3>
      <p class="mb-4 max-w-md text-center text-sm text-gray-600">
        We encountered an issue while processing your request. Please start a new search.
      </p>
      <p
        v-if="error?.details"
        class="mb-4 rounded bg-gray-50 px-3 py-1.5 text-center font-mono text-xs text-gray-500"
      >
        {{ error.details }}
      </p>
      <AaButton
        @click="handleRestart"
        variant="secondary"
        size="medium"
        prepend-icon="i-material-symbols-refresh"
      >
        Start New Search
      </AaButton>
    </div>
  </div>
</template>

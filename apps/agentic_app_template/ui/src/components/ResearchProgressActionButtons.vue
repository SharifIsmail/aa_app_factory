<script setup lang="ts">
import { AaButton } from '@aleph-alpha/ds-components-vue';
import { defineProps, defineEmits } from 'vue';

defineProps<{
  structuredData: Record<string, any> | null;
}>();

const emit = defineEmits<{
  (e: 'view-report'): void;
  (e: 'download-report'): void;
  (e: 'start-new-search'): void;
}>();

const handleViewReport = () => {
  emit('view-report');
};

const handleDownloadReport = () => {
  emit('download-report');
};

const handleStartNewSearch = () => {
  emit('start-new-search');
};
</script>

<template>
  <div
    class="action-buttons mb-4 flex flex-col items-center justify-center rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 p-8 shadow-md"
  >
    <span
      class="success-icon i-material-symbols-task-alt-rounded bg-semantic-bg-success mb-6 text-8xl"
    />
    <div class="mb-8 max-w-md text-center">
      <h3 class="mb-3 text-2xl font-bold text-gray-800">Analysis Completed!</h3>
      <p class="text-lg text-gray-600">Your research report is now ready.</p>
    </div>
    <div class="flex max-w-xl flex-col justify-center gap-4 sm:flex-row">
      <AaButton
        @click="handleViewReport"
        variant="secondary"
        size="medium"
        prepend-icon="i-material-symbols-open-in-new"
        class="flex-1"
      >
        View Report
      </AaButton>
      <AaButton
        v-if="!structuredData"
        @click="handleDownloadReport"
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-download"
        class="flex-1"
      >
        Download Report as HTML
      </AaButton>
    </div>

    <div class="mt-6">
      <AaButton
        @click="handleStartNewSearch"
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-add"
      >
        Start a New Search
      </AaButton>
    </div>
  </div>
</template>

<style scoped>
/* Action buttons styles */
.action-buttons {
  min-height: 400px;
  transition: all 0.3s ease-in-out;
  padding-top: 3rem;
  padding-bottom: 3rem;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

.success-icon {
  animation: pulse 2s ease-in-out infinite;
}
</style>

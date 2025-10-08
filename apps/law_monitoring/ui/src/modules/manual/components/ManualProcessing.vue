<script setup lang="ts">
import ManualCompleted from './ManualCompleted.vue';
import ManualInput from './ManualInput.vue';
import ManualProcessingProgress from './ManualProcessingProgress.vue';
import { useManualReportGenerationStore } from '@/modules/manual/stores/useManualReportGenerationStore.ts';
import { onMounted, onBeforeUnmount } from 'vue';

// No props needed

const manualReportStore = useManualReportGenerationStore();

onMounted(() => {
  manualReportStore.resumePollingIfNeeded();
});

onBeforeUnmount(() => {
  manualReportStore.stopStatusPolling();
});
</script>

<template>
  <div class="flex h-60 flex-col items-center gap-4">
    <!-- Input form - hidden during processing -->
    <ManualInput
      v-if="!manualReportStore.showProgress && !manualReportStore.showCompleted"
      :law-url="manualReportStore.lawUrl"
      @update:law-url="manualReportStore.lawUrl = $event"
      :url-error="manualReportStore.urlError"
      :is-computing-summary="manualReportStore.isComputingSummary"
      @generate-report="manualReportStore.generateLawReport"
    />

    <!-- Progress section -->
    <ManualProcessingProgress
      v-if="manualReportStore.showProgress"
      :progress-percentage="manualReportStore.progressPercentage"
      :task-counter="manualReportStore.taskCounter"
      :current-task="manualReportStore.currentTask"
      @stop-search="manualReportStore.stopSearch"
      class="w-180"
    />

    <!-- Completed actions -->
    <ManualCompleted
      v-if="manualReportStore.showCompleted"
      :search-id="manualReportStore.searchId!"
      @view-report="manualReportStore.handleViewReport"
      @download-report="manualReportStore.handleDownloadReport"
      @download-word-report="manualReportStore.handleDownloadWordReport"
      @download-pdf-report="manualReportStore.handleDownloadPdfReport"
      @start-new-search="manualReportStore.handleStartNewSearch"
    />
  </div>
</template>

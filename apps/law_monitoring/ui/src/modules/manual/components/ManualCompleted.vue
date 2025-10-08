<script setup lang="ts">
import { AaButton, AaText } from '@aleph-alpha/ds-components-vue';

interface Emits {
  (e: 'view-report'): void;
  (e: 'download-report'): void;
  (e: 'download-word-report'): void;
  (e: 'download-pdf-report'): void;
  (e: 'start-new-search'): void;
}

const emit = defineEmits<Emits>();

const handleViewReport = () => {
  emit('view-report');
};

const handleDownloadReport = () => {
  emit('download-report');
};

const handleDownloadWordReport = () => {
  emit('download-word-report');
};

const handleDownloadPdfReport = () => {
  emit('download-pdf-report');
};

const handleStartNewSearch = () => {
  emit('start-new-search');
};
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-6 p-2">
    <div></div>
    <div class="text-center">
      <AaText element="h2" size="lg" weight="semibold" class="mb-2">Analysis Completed!</AaText>
      <AaText element="p" size="sm" class="text-core-content-secondary">
        Your law analysis report is now ready.
      </AaText>
    </div>
    <div class="flex flex-wrap justify-center gap-4">
      <AaButton
        @click="handleViewReport"
        size="medium"
        prepend-icon="i-material-symbols-open-in-new-rounded"
      >
        View Report
      </AaButton>
      <AaButton
        @click="handleDownloadReport"
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-download"
      >
        Download HTML
      </AaButton>
      <AaButton
        @click="handleDownloadWordReport"
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-description"
      >
        Download Word
      </AaButton>
      <AaButton
        @click="handleDownloadPdfReport"
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-picture-as-pdf"
      >
        Download PDF
      </AaButton>
    </div>
    <div class="flex justify-center">
      <AaButton
        @click="handleStartNewSearch"
        variant="secondary"
        size="medium"
        prepend-icon="i-material-symbols-add"
        class="w-48"
      >
        Start New Analysis
      </AaButton>
    </div>
  </div>
</template>

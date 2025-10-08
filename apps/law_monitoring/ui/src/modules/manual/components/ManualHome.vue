<script setup lang="ts">
import ManualProcessing from '@/modules/manual/components/ManualProcessing.vue';
import { useManualReportGenerationStore } from '@/modules/manual/stores/useManualReportGenerationStore.ts';
import { AaButton, AaModal } from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

const manualReportStore = useManualReportGenerationStore();
const showModal = ref(false);

const openModal = () => {
  showModal.value = true;
  manualReportStore.resumePollingIfNeeded();
};

const closeModal = () => {
  showModal.value = false;
};

// Button text based on generation state
const buttonText = computed(() => {
  return manualReportStore.isGenerating ? 'Generating Report...' : 'Manual Generation of Reports';
});
</script>

<template>
  <div class="flex flex-col items-end gap-6">
    <AaButton
      variant="outline"
      size="medium"
      prepend-icon="i-material-symbols-quick-reference-all-outline"
      :loading="manualReportStore.isGenerating"
      @click="openModal"
      >{{ buttonText }}</AaButton
    >

    <Teleport to="body">
      <AaModal
        v-if="showModal"
        title="Manual Generation of Reports"
        with-overlay
        @close="closeModal"
      >
        <div class="flex w-[800px] flex-col overflow-hidden">
          <div class="flex-1 overflow-y-auto p-6">
            <ManualProcessing />
          </div>
        </div>
      </AaModal>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { openContentInNewWindow } from '@/@core/utils/fileUtils.ts';
import { manualLawAnalysisService } from '@/@core/utils/http.ts';
import type { PreprocessedLaw } from 'src/modules/monitoring/types';

interface Props {
  law: PreprocessedLaw;
}

const props = defineProps<Props>();
const notificationStore = useNotificationStore();

const openFullReport = async () => {
  if (!props.law?.law_file_id) return;

  try {
    const uuid = props.law.law_file_id.replace(/^law_/, ''); // Remove 'law_' prefix for backend compatibility
    const html = await manualLawAnalysisService.getReport(uuid, false, 'html');
    openContentInNewWindow(html, { mimeType: 'text/html' });
  } catch (error) {
    console.error('Failed to fetch report:', error);
    notificationStore.addErrorNotification('Failed to open report. Please try again.');
  }
};

// Expose the openFullReport function to parent components
defineExpose({
  openFullReport,
});
</script>

<template>
  <!-- This component doesn't render anything visible, it just provides the HTML report functionality -->
  <div style="display: none"></div>
</template>

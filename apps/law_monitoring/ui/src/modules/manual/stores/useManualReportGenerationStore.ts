import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { openContentInNewWindow, downloadContentAsFile } from '@/@core/utils/fileUtils.ts';
import { manualLawAnalysisService } from '@/@core/utils/http.ts';
import { useTaskProgress, type Task } from '@/modules/manual/composables/useTaskProgress.ts';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useManualReportGenerationStore = defineStore(
  createStoreId('manualReportGeneration'),
  () => {
    const notificationStore = useNotificationStore();

    const lawUrl = ref('');
    const urlError = ref('');
    const isComputingSummary = ref(false);

    const searchId = ref<string | null>(null);
    const searchStatus = ref<'COMPLETED' | 'FAILED' | 'IN_PROGRESS' | null>(null);
    const tasks = ref<Task[]>([]);
    const statusPollInterval = ref<ReturnType<typeof setInterval> | null>(null);

    const isValidUrl = computed(() => {
      if (!lawUrl.value) return true;
      return lawUrl.value.includes('eur-lex.europa.eu');
    });

    const { progressPercentage, taskCounter, currentTask } = useTaskProgress(tasks, searchStatus);

    const showProgress = computed(() => {
      return (
        searchId.value && searchStatus.value !== 'COMPLETED' && searchStatus.value !== 'FAILED'
      );
    });

    const showCompleted = computed(() => {
      return searchStatus.value === 'COMPLETED';
    });

    const hasActiveProcess = computed(() => {
      return isComputingSummary.value || searchId.value !== null;
    });

    const isGenerating = computed(() => {
      return (
        isComputingSummary.value ||
        !!(searchId.value && searchStatus.value !== 'COMPLETED' && searchStatus.value !== 'FAILED')
      );
    });

    const generateLawReport = async () => {
      if (!lawUrl.value.trim() || !isValidUrl.value) return;

      urlError.value = '';
      isComputingSummary.value = true;
      try {
        const response = await manualLawAnalysisService.startLawSummary(lawUrl.value);
        searchId.value = response.id;
        searchStatus.value = 'IN_PROGRESS';
        startStatusPolling();
      } catch (error: any) {
        console.error('Error:', error);
        urlError.value = error.message || 'An error occurred. Please try again.';
      } finally {
        isComputingSummary.value = false;
      }
    };

    const fetchStatus = async () => {
      if (!searchId.value) return;

      try {
        const response = await manualLawAnalysisService.getSummaryStatus(searchId.value);
        searchStatus.value = response.status;
        tasks.value = response.tasks || [];

        // Stop polling when completed or failed
        if (['COMPLETED', 'FAILED'].includes(response.status)) {
          stopStatusPolling();
        }
      } catch (error) {
        console.error('Error fetching search status:', error);
        stopStatusPolling();
      }
    };

    const startStatusPolling = () => {
      fetchStatus(); // Initial fetch
      statusPollInterval.value = setInterval(() => {
        fetchStatus();
      }, 1000); // Poll every second
    };

    const stopStatusPolling = () => {
      if (statusPollInterval.value) {
        clearInterval(statusPollInterval.value);
        statusPollInterval.value = null;
      }
    };

    const stopSearch = async () => {
      if (!searchId.value) return;

      try {
        await manualLawAnalysisService.stopSummary(searchId.value);
        searchId.value = null;
        searchStatus.value = null;
        tasks.value = [];
      } catch (error) {
        console.error('Error stopping search:', error);
      } finally {
        stopStatusPolling();
      }
    };

    const resumePollingIfNeeded = () => {
      if (searchId.value && !statusPollInterval.value) {
        if (searchStatus.value === null || searchStatus.value === 'IN_PROGRESS') {
          startStatusPolling();
        }
      }
    };

    // Action handlers for completed state
    const handleViewReport = async () => {
      if (!searchId.value) return;
      try {
        const html = await manualLawAnalysisService.getReport(searchId.value, false);
        openContentInNewWindow(html, { mimeType: 'text/html' });
      } catch (error) {
        console.error('Failed to fetch report:', error);
        notificationStore.addErrorNotification('Failed to open report. Please try again.');
      }
    };

    const handleDownloadReport = async () => {
      if (!searchId.value) return;
      try {
        const html = await manualLawAnalysisService.getReport(searchId.value, true);
        downloadContentAsFile(html, `law_report_${searchId.value}.html`, {
          mimeType: 'text/html charset=utf-8',
        });
      } catch (error) {
        console.error('Failed to download report:', error);
        notificationStore.addErrorNotification('Failed to download report. Please try again.');
      }
    };

    const handleDownloadWordReport = async () => {
      if (!searchId.value) return;
      try {
        const wordContent = await manualLawAnalysisService.getReport(
          searchId.value,
          true,
          'docx',
          true
        );
        downloadContentAsFile(wordContent, `law_report_${searchId.value}.docx`, {
          mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        });
      } catch (error) {
        console.error('Failed to download Word report:', error);
        notificationStore.addErrorNotification('Failed to download Word report. Please try again.');
      }
    };

    const handleDownloadPdfReport = async () => {
      if (!searchId.value) return;
      try {
        const pdfContent = await manualLawAnalysisService.getReport(
          searchId.value,
          true,
          'pdf',
          true
        );
        downloadContentAsFile(pdfContent, `law_report_${searchId.value}.pdf`, {
          mimeType: 'application/pdf',
        });
      } catch (error) {
        console.error('Failed to download PDF report:', error);
        notificationStore.addErrorNotification('Failed to download PDF report. Please try again.');
      }
    };

    const handleStartNewSearch = () => {
      stopStatusPolling();
      searchId.value = null;
      searchStatus.value = null;
      tasks.value = [];
      lawUrl.value = '';
      urlError.value = '';
    };

    const resetState = () => {
      stopStatusPolling();
      lawUrl.value = '';
      urlError.value = '';
      isComputingSummary.value = false;
      searchId.value = null;
      searchStatus.value = null;
      tasks.value = [];
    };

    return {
      // State
      lawUrl,
      urlError,
      isComputingSummary,
      searchId,
      searchStatus,
      tasks,

      // Computed
      isValidUrl,
      progressPercentage,
      taskCounter,
      currentTask,
      showProgress,
      showCompleted,
      hasActiveProcess,
      isGenerating,

      // Actions
      generateLawReport,
      fetchStatus,
      startStatusPolling,
      stopStatusPolling,
      stopSearch,
      resumePollingIfNeeded,
      handleViewReport,
      handleDownloadReport,
      handleDownloadWordReport,
      handleDownloadPdfReport,
      handleStartNewSearch,
      resetState,
    };
  }
);

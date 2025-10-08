import { createStoreId } from './createStoreId';
import { HTTP_CLIENT } from '@/utils/http';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

type DataPreparationStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

interface DataPreparationStatusResponse {
  status: DataPreparationStatus;
  error?: string | null;
}

export const useDataPreparationStore = defineStore(createStoreId('data-preparation'), () => {
  const status = ref<DataPreparationStatus>('pending');
  const error = ref<string | null>(null);
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null);
  const consecutiveFailures = ref(0);

  const isReady = computed(() => status.value === 'completed');
  const isLoading = computed(() => status.value === 'in_progress');
  const hasFailed = computed(() => status.value === 'failed');
  const isOverlayVisible = computed(
    () => status.value === 'in_progress' || status.value === 'failed'
  );

  const updateStatus = (newStatus: { status: DataPreparationStatus; error?: string | null }) => {
    status.value = newStatus.status;
    error.value = newStatus.error || null;
  };

  const fetchStatus = async () => {
    try {
      const response =
        await HTTP_CLIENT.get<DataPreparationStatusResponse>('data-preparation-status');
      updateStatus(response.data);

      consecutiveFailures.value = 0;

      if (response.data.status === 'completed' || response.data.status === 'failed') {
        stopPolling();
      }
    } catch (error) {
      console.error('Failed to fetch data preparation status:', error);
      consecutiveFailures.value++;

      if (consecutiveFailures.value >= 3) {
        updateStatus({
          status: 'failed',
          error:
            'Der Status der Datenvorbereitung konnte nach mehreren Versuchen nicht abgerufen werden. Bitte überprüfen Sie Ihre Verbindung und versuchen Sie es erneut.',
        });
        stopPolling();
      }
    }
  };

  const startPolling = () => {
    consecutiveFailures.value = 0;
    fetchStatus();
    pollingInterval.value = setInterval(fetchStatus, 2000);
  };

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value);
      pollingInterval.value = null;
    }
  };

  return {
    status,
    error,
    isReady,
    isLoading,
    hasFailed,
    isOverlayVisible,
    updateStatus,
    startPolling,
    stopPolling,
  };
});

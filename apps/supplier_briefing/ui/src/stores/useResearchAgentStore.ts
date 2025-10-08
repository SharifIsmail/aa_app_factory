import { createStoreId } from './createStoreId';
import type {
  Task,
  ResearchStatusResponse,
  SearchCompleteCallback,
  SearchCompleteData,
} from '@/types';
import { researchAgentService } from '@/utils/http';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useResearchAgentStore = defineStore(createStoreId('research-agent'), () => {
  // State
  const activeSearchId = ref<string | null>(null);
  const researchStatus = ref<ResearchStatusResponse | null>(null);
  const isLoading = ref(false);
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null);
  const consecutiveStatusFailures = ref(0);
  const MAX_STATUS_FETCH_RETRIES = 3;

  // Individual callback system
  const successCallback = ref<SearchCompleteCallback<SearchCompleteData> | null>(null);
  const failureCallback = ref<() => void>(() => {});
  const statusCallback = ref<SearchCompleteCallback<ResearchStatusResponse> | null>(null);

  // Computed
  const isActive = computed(() => activeSearchId.value !== null);
  const currentTask = computed(() => {
    if (!researchStatus.value?.tasks) return null;

    const findInProgressTask = (tasks: Task[]): Task | null => {
      for (const task of tasks) {
        if (task.status === 'IN_PROGRESS') return task;
        if (task.subtasks) {
          const inProgressSubtask = findInProgressTask(task.subtasks);
          if (inProgressSubtask) return inProgressSubtask;
        }
      }
      return null;
    };

    return findInProgressTask(researchStatus.value.tasks);
  });

  async function startResearch(
    researchTopic: string,
    onSuccess: SearchCompleteCallback<SearchCompleteData>,
    onFailure: () => void,
    onStatusUpdate?: SearchCompleteCallback<ResearchStatusResponse>,
    executionId?: string,
    flowName?: string,
    params?: object
  ): Promise<string | null> {
    try {
      isLoading.value = true;

      // Store the callbacks
      successCallback.value = onSuccess;
      failureCallback.value = onFailure;
      statusCallback.value = onStatusUpdate || null;

      const response = await researchAgentService.startResearchAgent(
        researchTopic,
        executionId,
        flowName,
        params
      );

      if (response?.id) {
        activeSearchId.value = response.id;
        consecutiveStatusFailures.value = 0;
        startPolling();
        return response.id;
      }

      throw new Error('No search ID received from server');
    } catch (err: any) {
      console.error('Error starting research:', err);
      failureCallback.value();

      return null;
    } finally {
      isLoading.value = false;
    }
  }

  function getResearchAnswer(response: ResearchStatusResponse): string {
    const answer = response.final_result?.agent_response;

    if (!answer) return 'Keine Ergebnisse abgerufen';

    if (typeof answer === 'string') return answer;

    if (answer && answer.data) return answer.data;

    return JSON.stringify(answer, null, 2);
  }

  async function fetchStatus(): Promise<void> {
    if (!activeSearchId.value) return;

    try {
      const response = await researchAgentService.getResearchAgentStatus(activeSearchId.value);

      researchStatus.value = response;
      // reset transient failure counter on any successful response
      consecutiveStatusFailures.value = 0;

      // Call status callback on every poll if provided
      if (statusCallback.value) {
        statusCallback.value(response);
      }

      if (['COMPLETED', 'FAILED'].includes(response.status)) {
        stopPolling();

        if (response.status === 'COMPLETED') {
          const completionData: SearchCompleteData = {
            answer: getResearchAnswer(response),
            pandasObjectsData: response.pandas_objects_data,
            explained_steps: response.explained_steps,
            resultsData: response.results_data,
          };

          // Call success callback if provided
          if (successCallback.value) {
            successCallback.value(completionData);
          }
        }

        if (response.status === 'FAILED') {
          failureCallback.value();
          return;
        }
      }
    } catch (err: any) {
      console.error('Error fetching search status:', err);
      consecutiveStatusFailures.value += 1;
      if (consecutiveStatusFailures.value >= MAX_STATUS_FETCH_RETRIES) {
        stopPolling();
        failureCallback.value();
      }
    }
  }

  function startPolling(): void {
    if (pollingInterval.value) return;

    fetchStatus();
    pollingInterval.value = setInterval(fetchStatus, 1000);
  }

  function stopPolling(): void {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value);
      pollingInterval.value = null;
    }
  }

  async function stopResearch(): Promise<boolean> {
    if (!activeSearchId.value) return false;

    try {
      isLoading.value = true;
      await researchAgentService.stopResearchAgent(activeSearchId.value);

      stopPolling();
      reset();
      return true;
    } catch (err: any) {
      console.error('Error stopping research:', err);

      return false;
    } finally {
      isLoading.value = false;
    }
  }

  function reset(): void {
    activeSearchId.value = null;
    researchStatus.value = null;
    successCallback.value = null;
    failureCallback.value = () => {};
    statusCallback.value = null;
    stopPolling();
  }

  return {
    // State
    isLoading,
    researchStatus,
    // Computed
    isActive,
    currentTask,

    // Actions
    startResearch,
    fetchStatus,
    stopResearch,
    reset,
  };
});

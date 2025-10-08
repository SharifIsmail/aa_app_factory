<script setup lang="ts">
import { useTaskProgress, type Task } from '../composables/useTaskProgress';
import { researchAgentService } from '../utils/http';
import ResearchProgressActionButtons from './ResearchProgressActionButtons.vue';
import ResearchProgressBar from './ResearchProgressBar.vue';
import ResearchProgressDataPanel from './ResearchProgressDataPanel.vue';
import ResearchProgressError from './ResearchProgressError.vue';
import ResearchProgressTaskPanel from './ResearchProgressTaskPanel.vue';
import ResearchProgressTerminal from './ResearchProgressTerminal.vue';
import { useSearchStore } from '@/stores/useSearchStore.ts';
import { ref, onMounted, onBeforeUnmount } from 'vue';

const props = defineProps<{
  searchId: string | null;
}>();

const emit = defineEmits<{
  (e: 'stop-search'): void;
}>();

const searchStatus = ref<string | null>(null);
const tasks = ref<Task[]>([]);
const currentTask = ref<Task | null>(null);
const toolLogs = ref<any[]>([]);
const extractedData = ref<string | null>(null);
const structuredData = ref<Record<string, any> | null>(null);
const error = ref<{ message: string; details?: any } | null>(null);
const statusPollInterval = ref<ReturnType<typeof setInterval> | null>(null);

const { progressPercentage, taskCounter } = useTaskProgress(tasks, currentTask, searchStatus);

const searchStore = useSearchStore();

const fetchStatus = async () => {
  if (!props.searchId) return;
  try {
    const response = await researchAgentService.getResearchAgentStatus(props.searchId);

    error.value = null;
    console.log('Full response from API:', response);

    searchStatus.value = response.status;
    console.log('Search status updated to:', searchStatus.value);

    tasks.value = response.tasks || [];
    console.log('Tool logs received:', response.tool_logs);
    toolLogs.value = response.tool_logs || [];

    if (response.extracted_data) {
      structuredData.value = response.extracted_data;
      extractedData.value = null;
    }

    findInProgressTask();
    if (['COMPLETED', 'FAILED'].includes(response.status)) {
      stopStatusPolling();
    }
  } catch (error: any) {
    console.error('Error fetching search status:', error);
    const axiosError = error as {
      response?: { status: number; statusText: string };
      config?: { url?: string };
    };
    error.value = {
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      details: axiosError.response
        ? `${axiosError.response.status} ${axiosError.response.statusText} - ${axiosError.config?.url || 'unknown URL'}`
        : 'Failed to connect to server',
    };
    stopStatusPolling();
  }
};

const findInProgressTask = () => {
  const findInProgressInList = (taskList?: Task[]): Task | null => {
    if (!taskList) return null;
    for (const task of taskList) {
      if (task.status === 'IN_PROGRESS') return task;
      if (task.subtasks) {
        const inProgressSubtask = findInProgressInList(task.subtasks);
        if (inProgressSubtask) return inProgressSubtask;
      }
    }
    return null;
  };
  currentTask.value = findInProgressInList(tasks.value);
};

const startStatusPolling = () => {
  fetchStatus();
  statusPollInterval.value = setInterval(fetchStatus, 1000);
};

const stopStatusPolling = () => {
  if (statusPollInterval.value) {
    clearInterval(statusPollInterval.value);
    statusPollInterval.value = null;
  }
};

const stopSearch = async () => {
  if (!props.searchId) return;
  try {
    await researchAgentService.stopResearchAgent(props.searchId);
    emit('stop-search');
    setTimeout(() => window.location.reload(), 100);
  } catch (err) {
    console.error('Error stopping search:', err);
    emit('stop-search');
    setTimeout(() => window.location.reload(), 100);
  } finally {
    stopStatusPolling();
  }
};

const handleViewReport = async () => {
  if (!props.searchId) return;
  try {
    const html = await researchAgentService.getReport(props.searchId, false);
    const blob = new Blob([html], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
  } catch (error) {
    console.error('Failed to fetch report:', error);
  }
};

const handleDownloadReport = async () => {
  if (!props.searchId) return;
  try {
    const html = await researchAgentService.getReport(props.searchId, true);
    const blob = new Blob([html], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${props.searchId}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to download report:', error);
  }
};

const handleStartNewSearch = () => {
  if (!props.searchId) return;
  emit('stop-search');
};

const handleRestart = () => {
  stopStatusPolling();
  emit('stop-search');
  searchStore.clearSearchId();
};

onMounted(startStatusPolling);
onBeforeUnmount(stopStatusPolling);
</script>

<template>
  <div class="mx-auto flex w-[1000px] flex-col gap-3">
    <ResearchProgressBar
      v-if="searchStatus !== 'COMPLETED'"
      :search-status="searchStatus"
      :task-counter="taskCounter"
      :current-task="currentTask"
      :progress-percentage="progressPercentage"
      @stop-search="stopSearch"
    />

    <!-- Error message section -->
    <ResearchProgressError v-if="error" :error="error" @restart="handleRestart" />

    <!-- Data Panel Component -->
    <ResearchProgressDataPanel
      :structured-data="structuredData"
      :extracted-data="extractedData"
      :search-status="searchStatus"
    />
    <ResearchProgressTerminal
      v-if="searchStatus !== 'COMPLETED'"
      :search-status="searchStatus"
      :tool-logs="toolLogs"
    />

    <!-- Action buttons panel (shown when all tasks are completed) -->
    <ResearchProgressActionButtons
      v-if="searchStatus === 'COMPLETED'"
      :structured-data="structuredData"
      @view-report="handleViewReport"
      @download-report="handleDownloadReport"
      @start-new-search="handleStartNewSearch"
    />

    <!-- Task panel -->
    <ResearchProgressTaskPanel :tasks="tasks" :search-status="searchStatus" />
  </div>
</template>

<style scoped>
@keyframes bounce {
  0%,
  100% {
    left: 0;
    animation-timing-function: ease-in-out;
  }
  50% {
    left: calc(100% - 40px);
  }
}

@keyframes bounceReverse {
  0%,
  100% {
    right: 0;
    animation-timing-function: ease-in-out;
  }
  50% {
    right: calc(100% - 32px);
  }
}

@keyframes progress {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes pulseDot {
  0%,
  100% {
    opacity: 0.3;
    transform: translateY(-50%) scale(0.8);
  }
  50% {
    opacity: 1;
    transform: translateY(-50%) scale(1.1);
  }
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes bubble {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}
</style>

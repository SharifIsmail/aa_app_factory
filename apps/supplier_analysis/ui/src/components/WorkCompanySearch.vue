<script lang="ts">
import { useTaskProgress, type Task } from '../composables/useTaskProgress';
import { companyDataService } from '../utils/http';
import { storageUtils } from '../utils/storage';
import TaskItem from './TaskItem.vue';
import { AaText } from '@aleph-alpha/ds-components-vue';
import { defineComponent, ref, computed } from 'vue';

export default defineComponent({
  components: {
    TaskItem,
    AaText,
  },
  props: {
    searchId: {
      type: String as () => string | null,
      required: true,
    },
    isRisks: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['stop-search'],
  setup() {
    const searchStatus = ref(null);
    const tasks = ref<Task[]>([]);
    const currentTask = ref<Task | null>(null);
    const toolLogs = ref<any[]>([]);
    const isTerminalExpanded = ref(false);
    const isDataPanelExpanded = ref(false);
    const hideCompletedTasks = ref(true);
    const extractedData = ref<string | null>(null);
    const structuredData = ref<Record<string, any> | null>(null);
    const error = ref<{ message: string; details?: any } | null>(null);

    // Computed property to check if all tool logs have results
    const allToolLogsHaveResults = computed(() => {
      return toolLogs.value.length > 0 && toolLogs.value.every((log) => log.result);
    });

    // Computed property to check if all tasks are completed
    const allTasksCompleted = computed(() => {
      // Consider all tasks as completed if the search status is 'COMPLETED'
      // OR if ALL tasks have status 'COMPLETED' and there are tasks
      return (
        searchStatus.value === 'COMPLETED' ||
        (tasks.value.length > 0 && tasks.value.every((task) => task.status === 'COMPLETED'))
      );
    });

    // Reuse the functions from useTaskProgress
    const countCompletedTasks = (taskList: Task[]): number => {
      let count = 0;
      for (const task of taskList) {
        if (task.status === 'COMPLETED') {
          count++;
        }
        if (task.subtasks) {
          count += countCompletedTasks(task.subtasks);
        }
      }
      return count;
    };

    // Helper function to recursively filter out completed tasks
    const filterCompletedTasks = (taskList: Task[]): Task[] => {
      return taskList
        .filter((task) => task.status !== 'COMPLETED')
        .map((task) => {
          // Create a new task object with filtered subtasks
          if (task.subtasks && task.subtasks.length > 0) {
            return {
              ...task,
              subtasks: filterCompletedTasks(task.subtasks),
            };
          }
          return task;
        });
    };

    // Computed property to filter tasks based on hideCompletedTasks state
    const visibleTasks = computed(() => {
      if (!hideCompletedTasks.value) {
        return tasks.value;
      }
      // Recursively filter completed tasks at all levels
      return filterCompletedTasks(tasks.value);
    });

    // Computed property to count completed tasks recursively
    const completedTasksCount = computed(() => {
      return countCompletedTasks(tasks.value);
    });

    // Use the extracted composable for task progress tracking
    const { progressPercentage, taskCounter } = useTaskProgress(tasks, currentTask, searchStatus);

    const makeUrlsClickable = (text: string) => {
      if (!text) return text;
      // Improved URL regex: only match the URL, not trailing punctuation
      const urlRegex = /(https?:\/\/[\w\-._~:/?#[\]@!$&'()*+,;=%]+[\w\-_/])/g;
      return text.replace(urlRegex, (url) => {
        return `<a href="${url}" target="_blank" class="text-blue-500 hover:text-blue-700 hover:underline">${url}</a>`;
      });
    };

    const renderStructuredValue = (value: any) => {
      const raw = value && typeof value === 'object' ? value.value : value;
      if (isDataPanelExpanded.value) {
        return makeUrlsClickable(
          raw
            ?.replace(/(^|[^<br>\n])Source URL:/g, function (match: string, p1: string) {
              return p1 === '' || p1 === '\n' || p1.endsWith('<br>')
                ? p1 + 'Source URL:'
                : p1 + '<br>Source URL:';
            })
            ?.replace(/\n/g, '<br>')
        );
      } else {
        return makeUrlsClickable(raw);
      }
    };

    return {
      searchStatus,
      tasks,
      currentTask,
      progressPercentage,
      taskCounter,
      toolLogs,
      isTerminalExpanded,
      isDataPanelExpanded,
      allToolLogsHaveResults,
      hideCompletedTasks,
      visibleTasks,
      completedTasksCount,
      extractedData,
      structuredData,
      allTasksCompleted,
      error,
      makeUrlsClickable,
      renderStructuredValue,
    };
  },
  data() {
    return {
      statusPollInterval: null as ReturnType<typeof setInterval> | null,
    };
  },
  mounted() {
    this.startStatusPolling();
  },
  beforeUnmount() {
    this.stopStatusPolling();
  },
  methods: {
    async fetchStatus() {
      if (!this.searchId) return;

      try {
        let response;
        if (this.isRisks) {
          response = await companyDataService.getCompanyRisksResearchStatus(this.searchId);
        } else {
          response = await companyDataService.getCompanyDataSearchStatus(this.searchId);
        }

        // Clear any previous errors
        this.error = null;

        // Log the entire response for debugging
        console.log('Full response from API:', response);

        // Explicitly set the status from the response
        this.searchStatus = response.status;
        console.log('Search status updated to:', this.searchStatus);

        this.tasks = response.tasks || [];

        // Explicitly log and assign tool logs
        console.log('Tool logs received:', response.tool_logs);
        this.toolLogs = response.tool_logs || [];

        // Handle extracted data properly
        if (response.extracted_data) {
          // Assign the entire extracted_data object as structuredData
          this.structuredData = response.extracted_data;
          // We don't need extractedData anymore since we're using structuredData
          this.extractedData = null;
        }

        this.findInProgressTask();

        // If search is completed or failed, stop polling
        if (['COMPLETED', 'FAILED'].includes(response.status)) {
          this.stopStatusPolling();
        }
      } catch (error) {
        console.error('Error fetching search status:', error);
        const axiosError = error as {
          response?: { status: number; statusText: string };
          config?: { url?: string };
        };
        this.error = {
          message: error instanceof Error ? error.message : 'Unknown error occurred',
          details: axiosError.response
            ? `${axiosError.response.status} ${axiosError.response.statusText} - ${axiosError.config?.url || 'unknown URL'}`
            : 'Failed to connect to server',
        };
        this.stopStatusPolling();
      }
    },
    findInProgressTask() {
      // Function to find IN_PROGRESS tasks or subtasks
      const findInProgressInList = (taskList: Task[] | undefined): Task | null => {
        if (!taskList) return null;

        for (const task of taskList) {
          if (task.status === 'IN_PROGRESS') {
            return task;
          }

          // Check subtasks if present
          if (task.subtasks) {
            const inProgressSubtask = findInProgressInList(task.subtasks);
            if (inProgressSubtask) {
              return inProgressSubtask;
            }
          }
        }

        return null;
      };

      this.currentTask = findInProgressInList(this.tasks);
    },
    startStatusPolling() {
      this.fetchStatus(); // Initial fetch
      this.statusPollInterval = setInterval(() => {
        this.fetchStatus();
      }, 1000); // Poll every second
    },
    stopStatusPolling() {
      if (this.statusPollInterval) {
        clearInterval(this.statusPollInterval);
        this.statusPollInterval = null;
      }
    },
    async stopSearch() {
      if (!this.searchId) return;

      try {
        await companyDataService.stopCompanyDataSearch(this.searchId);
        this.$emit('stop-search'); // Emit event to parent to switch back to input screen

        // Allow time for the parent component to clear localStorage
        setTimeout(() => {
          // Reload the page to get a fresh state
          window.location.reload();
        }, 100);
      } catch (error) {
        console.error('Error stopping search:', error);
        this.$emit('stop-search'); // Still emit the event to clear localStorage

        // Also reload in case of errors
        setTimeout(() => {
          window.location.reload();
        }, 100);
      } finally {
        this.stopStatusPolling();
      }
    },
    async handleViewReport() {
      if (!this.searchId) return;
      try {
        const html = await companyDataService.getReport(this.searchId, 'data', false);
        const blob = new Blob([html], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
      } catch (error) {
        console.error('Failed to fetch report:', error);
        alert('Failed to open report. Please try again.');
      }
    },
    async handleViewRiskReport() {
      if (!this.searchId) return;
      try {
        const html = await companyDataService.getReport(this.searchId, 'risks', false);
        const blob = new Blob([html], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
      } catch (error) {
        console.error('Failed to fetch report:', error);
        alert('Failed to open report. Please try again.');
      }
    },
    async handleDownloadReport() {
      if (!this.searchId) return;
      try {
        const html = await companyDataService.getReport(this.searchId, 'data', true);
        const blob = new Blob([html], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report-${this.searchId}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Failed to download report:', error);
        alert('Failed to download report. Please try again.');
      }
    },
    async handleDownloadRiskReport() {
      if (!this.searchId) return;
      try {
        const html = await companyDataService.getReport(this.searchId, 'risks', true);
        const blob = new Blob([html], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report-${this.searchId}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Failed to download risk report:', error);
        alert('Failed to download risk report. Please try again.');
      }
    },
    handleStartNewSearch() {
      if (!this.searchId) return;
      this.$emit('stop-search');
    },
    handleRestart() {
      this.stopStatusPolling();
      this.$emit('stop-search'); // Emit event to parent to switch back to input screen
      storageUtils.clearSearchId();
    },
  },
});
</script>

<template>
  <div class="mx-auto flex h-full w-[1000px] flex-col">
    <!-- Progress bar section with v-if condition -->
    <div v-if="searchStatus !== 'COMPLETED'" class="mb-2 flex items-start gap-3">
      <div class="flex flex-grow flex-col overflow-hidden rounded-lg bg-white shadow-md">
        <div class="flex flex-row items-center p-2 pb-0">
          <span class="mr-2 whitespace-nowrap rounded-md bg-gray-100 px-2 py-1 text-xs">
            {{ taskCounter }}
          </span>
          <div class="flex-grow overflow-hidden">
            <div v-if="currentTask" class="truncate">
              <AaText weight="normal" class="text-sm">{{ currentTask.description }}</AaText>
            </div>
            <AaText weight="" v-else class="text-sm">Loading job status...</AaText>
          </div>
          <button
            @click="stopSearch"
            class="ml-3 flex-shrink-0 p-1 opacity-30 transition-opacity duration-200 hover:opacity-100"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="currentColor"
            >
              <path d="M6 6h12v12H6V6z" />
            </svg>
          </button>
        </div>

        <div class="flex items-center p-2">
          <div class="relative mr-3 h-2 flex-grow overflow-hidden rounded-full bg-gray-200">
            <div
              class="relative h-full overflow-hidden rounded-full bg-[#EEDC12]"
              :style="{ width: `${progressPercentage}%` }"
            >
              <div class="shimmer-effect absolute inset-0"></div>
            </div>
            <div
              v-if="currentTask"
              class="bubble-animation absolute top-0 h-2 w-2 rounded-full bg-white shadow-md"
              :style="{ left: `calc(${progressPercentage}% - 4px)` }"
            ></div>
          </div>
          <span class="whitespace-nowrap text-xs font-medium"> {{ progressPercentage }}% </span>
        </div>
      </div>
    </div>

    <!-- Error message section -->
    <div v-if="error" class="flex flex-col">
      <div class="mb-4 flex flex-col items-center rounded-lg border border-blue-100 bg-blue-50 p-6">
        <span class="mb-2 text-sm font-medium text-red-500">Error Message</span>
        <div class="mb-4 text-red-500">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="48"
            height="48"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <h3 class="mb-2 text-lg font-medium text-gray-800">We apologize for the interruption</h3>
        <p class="mb-4 max-w-md text-center text-sm text-gray-600">
          We encountered an issue while processing your request. Our team has been notified and
          we're working to resolve it. Please start a new search.
        </p>
        <p
          v-if="error.details"
          class="mb-4 rounded bg-gray-50 px-3 py-1.5 text-center font-mono text-xs text-gray-500"
        >
          {{ error.details }}
        </p>
        <button
          @click="handleRestart"
          class="flex items-center justify-center rounded-lg bg-blue-500 px-6 py-2 text-white shadow-sm transition duration-300 hover:bg-blue-600 hover:shadow-md"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-2"
          >
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
            <path d="M3 3v5h5"></path>
          </svg>
          <span class="font-medium">Start New Search</span>
        </button>
      </div>
    </div>

    <!-- Extracted Data Panel - hide when status is COMPLETED -->
    <div
      v-if="
        structuredData && Object.keys(structuredData).length > 0 && searchStatus !== 'COMPLETED'
      "
      class="research-data-panel relative mb-4 flex-shrink-0 rounded-lg bg-white text-sm shadow-md"
      :style="{
        height: isDataPanelExpanded ? 'auto' : '250px',
        padding: '8px',
        overflowY: 'scroll',
      }"
    >
      <div
        class="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white pb-1"
        :class="{ 'mb-2 px-2 pt-2': !isDataPanelExpanded, 'mb-3 p-2': isDataPanelExpanded }"
      >
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium text-gray-700">Data found so far</span>
          <span
            class="rounded-md border border-green-100 bg-green-50 px-3 py-1 text-sm font-medium text-green-700 shadow-sm"
          >
            {{ Object.keys(structuredData).length }} entries
          </span>
        </div>
        <button
          @click="isDataPanelExpanded = !isDataPanelExpanded"
          :class="[
            'flex items-center justify-center rounded p-1 transition-colors',
            isDataPanelExpanded ? 'bg-gray-200 hover:bg-gray-300' : 'bg-gray-100 hover:bg-gray-200',
          ]"
        >
          <svg
            v-if="isDataPanelExpanded"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
            class="text-gray-700"
          >
            <path
              d="M13.4 12l4.3-4.3a1 1 0 0 0-1.4-1.4L12 10.6 7.7 6.3a1 1 0 0 0-1.4 1.4l4.3 4.3-4.3 4.3a1 1 0 0 0 1.4 1.4l4.3-4.3 4.3 4.3a1 1 0 0 0 1.4-1.4L13.4 12z"
            />
          </svg>
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
            class="text-gray-700"
          >
            <path d="M3 3h7v7H3V3zm0 11h7v7H3v-7zm11 0h7v7h-7v-7zm0-11h7v7h-7V3z" />
          </svg>
          <span class="ml-1 text-xs text-gray-700">{{
            isDataPanelExpanded ? 'Collapse' : 'Expand'
          }}</span>
        </button>
      </div>

      <!-- Display structured data when available -->
      <div
        v-if="structuredData && Object.keys(structuredData).length > 0"
        :class="[
          isDataPanelExpanded
            ? 'grid grid-cols-1 gap-y-3 p-2'
            : 'grid grid-cols-1 gap-x-6 gap-y-2 px-2 pt-2 md:grid-cols-2 lg:grid-cols-3',
        ]"
      >
        <div
          v-for="(value, key) in structuredData"
          :key="key"
          :class="{
            'flex items-center overflow-hidden whitespace-nowrap border-b border-gray-100 py-1.5 pb-2':
              !isDataPanelExpanded,
            'flex flex-col border-b border-gray-100 pb-2': isDataPanelExpanded,
          }"
          :title="
            !isDataPanelExpanded
              ? key + ': ' + (typeof value === 'object' ? value.value : value)
              : ''
          "
        >
          <div
            :class="[
              'font-medium text-blue-600',
              isDataPanelExpanded ? 'mb-1' : 'mr-2 min-w-[130px] max-w-[130px] shrink-0 truncate',
            ]"
          >
            {{ key }}
          </div>
          <div
            :class="[
              'text-gray-700',
              isDataPanelExpanded ? 'break-words' : 'flex flex-1 items-center overflow-hidden',
            ]"
          >
            <span
              :class="[isDataPanelExpanded ? '' : 'inline-block max-w-[calc(100%-45px)] truncate']"
              v-html="renderStructuredValue(value)"
            >
            </span>
            <a
              v-if="value && typeof value === 'object' && value.source_url"
              :href="value.source_url"
              target="_blank"
              :class="[
                'text-xs text-gray-500 hover:text-blue-500 hover:underline',
                isDataPanelExpanded ? 'mt-1 block' : 'ml-1 inline-flex shrink-0 items-center',
              ]"
              :title="'Source: ' + value.source_url"
            >
              [source]
            </a>
          </div>
        </div>
      </div>

      <!-- Fallback to plain text display when structured data is not available -->
      <div v-else :class="['text-gray-700', isDataPanelExpanded ? 'p-4' : 'mt-2']">
        <div v-if="isDataPanelExpanded">
          <!-- In expanded view: preserve formatting and show full URLs -->
          <div v-for="(line, index) in extractedData?.split('\n') || []" :key="index" class="mb-2">
            <template v-if="line.includes('(SOURCE URL:')">
              <!-- Handle lines with source URLs -->
              <div>
                {{ line.split('(SOURCE URL:')[0].trim() }}
                <a
                  v-if="line.includes('(SOURCE URL:')"
                  :href="line.split('(SOURCE URL:')[1].replace(')', '').trim()"
                  target="_blank"
                  class="ml-2 text-xs text-gray-500 hover:text-blue-500 hover:underline"
                >
                  [source]
                </a>
              </div>
            </template>
            <template v-else>
              <!-- Regular lines without source URLs -->
              <div v-html="makeUrlsClickable(line)"></div>
            </template>
          </div>
        </div>
        <div v-else>
          <!-- In collapsed view: process each line to handle source URLs -->
          <div
            v-for="(line, index) in extractedData?.split('\n') || []"
            :key="index"
            class="truncate"
          >
            <template v-if="line.includes('(SOURCE URL:')">
              <span class="inline-block max-w-[calc(100%-45px)] truncate">
                {{ line.split('(SOURCE URL:')[0].trim() }}
              </span>
              <a
                :href="line.split('(SOURCE URL:')[1].replace(')', '').trim()"
                target="_blank"
                class="ml-1 inline-flex items-center text-xs text-gray-500 hover:text-blue-500 hover:underline"
              >
                [source]
              </a>
            </template>
            <template v-else>
              <span v-html="makeUrlsClickable(line)"></span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Terminal panel or Action buttons depending on search status -->
    <div
      v-if="searchStatus !== 'COMPLETED'"
      class="terminal-panel relative mb-4 flex-shrink-0 rounded-lg bg-gray-800/90 p-4 font-mono text-xs text-gray-400 shadow-md"
      :style="{
        height: isTerminalExpanded ? 'auto' : '180px',
        maxHeight: isTerminalExpanded ? '60vh' : 'none',
        overflowY: 'scroll',
      }"
    >
      <div
        class="sticky top-0 z-10 mb-1 flex items-center justify-between border-b border-gray-700 pb-1"
      >
        <span class="text-xs text-gray-300"></span>
        <button
          @click="isTerminalExpanded = !isTerminalExpanded"
          :class="[
            'flex items-center justify-center rounded p-1 transition-colors',
            isTerminalExpanded ? 'bg-gray-600 hover:bg-gray-500' : 'bg-gray-700 hover:bg-gray-600',
          ]"
        >
          <svg
            v-if="isTerminalExpanded"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
            class="text-gray-200"
          >
            <path
              d="M13.4 12l4.3-4.3a1 1 0 0 0-1.4-1.4L12 10.6 7.7 6.3a1 1 0 0 0-1.4 1.4l4.3 4.3-4.3 4.3a1 1 0 0 0 1.4 1.4l4.3-4.3 4.3 4.3a1 1 0 0 0 1.4-1.4L13.4 12z"
            />
          </svg>
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
            class="text-gray-200"
          >
            <path d="M3 3h7v7H3V3zm0 11h7v7H3v-7zm11 0h7v7h-7v-7zm0-11h7v7h-7V3z" />
          </svg>
          <span class="ml-1 text-xs text-gray-300">{{
            isTerminalExpanded ? 'Collapse' : 'Expand'
          }}</span>
        </button>
      </div>

      <!-- Display thinking indicator when no tool logs are available but search is in progress -->
      <div
        v-if="(!toolLogs || toolLogs.length === 0) && searchStatus === 'IN_PROGRESS'"
        class="mb-2 mt-1 flex items-baseline"
      >
        <span class="text-gray-500">$</span>
        <span class="ml-1 text-gray-300">{{
          new Date().toLocaleTimeString('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
          })
        }}</span>
        <span class="text-thinking-blink ml-1 flex items-center">
          <span class="thinking-pulse-dot mr-1.5"></span>
          <span class="font-medium">Thinking</span><span class="dot-1">.</span
          ><span class="dot-2">.</span><span class="dot-3">.</span>
        </span>
      </div>

      <!-- Display tool logs in reverse order -->
      <div v-if="toolLogs && toolLogs.length > 0" class="mt-1">
        <!-- Thinking indicator that appears only when all tool logs have results -->
        <div
          v-if="allToolLogsHaveResults && searchStatus === 'IN_PROGRESS'"
          class="mb-2 mt-1 flex items-baseline"
        >
          <span class="text-gray-500">$</span>
          <span class="ml-1 text-gray-300">{{
            new Date().toLocaleTimeString('en-GB', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false,
            })
          }}</span>
          <span class="text-thinking-blink ml-1 flex items-center">
            <span class="thinking-pulse-dot mr-1.5"></span>
            <span class="font-medium">Thinking</span><span class="dot-1">.</span
            ><span class="dot-2">.</span><span class="dot-3">.</span>
          </span>
        </div>

        <div
          v-for="(log, index) in [...toolLogs].reverse()"
          :key="index"
          class="mt-1 flex flex-col"
        >
          <div :class="['flex items-baseline', !log.result ? 'log-blink-container' : '']">
            <span class="text-gray-500">$</span>
            <span class="ml-1 text-gray-300">{{
              new Date(log.timestamp).toLocaleTimeString('en-GB', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
              })
            }}</span>
            <span
              :class="['ml-1', !log.result ? 'log-blink-text text-yellow-500' : 'text-yellow-500']"
              >{{ log.tool_name }}</span
            >
            <span v-for="(value, key) in log.params" :key="key" class="ml-1">
              <template v-if="value !== null && value !== undefined && value !== ''">
                <span class="text-gray-400">--{{ key }}=</span
                ><span :class="[!log.result ? 'log-blink-text text-teal-500' : 'text-teal-500']"
                  >"{{ value }}"</span
                >
              </template>
            </span>
          </div>

          <!-- Tool result display with height limit and gradient -->
          <div v-if="log.result" class="relative mb-2 mt-1">
            <div
              :class="[
                'overflow-hidden rounded',
                isTerminalExpanded ? '' : 'tool-result-container',
              ]"
            >
              <div
                :class="[
                  'white-space: pre-wrap word-break: break-word p-1',
                  isTerminalExpanded ? 'text-xs text-gray-300' : 'tool-result-content',
                ]"
              >
                {{ log.result }}
              </div>
              <div v-if="!isTerminalExpanded" class="tool-result-ellipsis">···</div>
            </div>
          </div>
          <div v-else class="log-loading mb-2 mt-1 pl-5 text-gray-500">
            <span class="dot-1">.</span><span class="dot-2">.</span><span class="dot-3">.</span>
          </div>
        </div>
      </div>

      <div class="mt-1 text-gray-500">user@lksg:~$ <span class="blink">_</span></div>
    </div>

    <!-- Action buttons panel (shown when all tasks are completed) - fix layout issues -->
    <div
      v-if="searchStatus === 'COMPLETED'"
      class="action-buttons mb-4 flex flex-grow flex-col items-center justify-center rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 p-8 shadow-md"
    >
      <div class="success-icon mb-6">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          width="64"
          height="64"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="text-green-500"
        >
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
      </div>
      <div class="mb-8 max-w-md text-center">
        <h3 class="mb-3 text-2xl font-bold text-gray-800">Analysis Completed!</h3>
        <p class="text-lg text-gray-600">Your company data report is now ready.</p>
      </div>
      <div class="flex w-full max-w-xl flex-col gap-4 sm:flex-row">
        <button
          v-if="structuredData && structuredData.hasOwnProperty('risk_incidents')"
          @click="() => handleViewReport()"
          class="action-button flex flex-1 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 px-6 py-4 text-base text-blue-700 shadow-sm transition duration-300 hover:bg-blue-100 hover:shadow-md"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="18"
            height="18"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-2"
          >
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
          <span class="font-bold">View Risk Report</span>
        </button>
        <button
          v-if="structuredData && structuredData.hasOwnProperty('risk_incidents')"
          @click="handleDownloadRiskReport"
          class="action-button flex flex-1 items-center justify-center rounded-lg border border-indigo-200 bg-indigo-50 px-6 py-4 text-base text-indigo-700 shadow-sm transition duration-300 hover:bg-indigo-100 hover:shadow-md"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="18"
            height="18"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span class="font-bold">Download Risk Report as HTML</span>
        </button>
        <button
          v-else
          @click="() => handleViewReport()"
          class="action-button flex flex-1 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 px-6 py-4 text-base text-blue-700 shadow-sm transition duration-300 hover:bg-blue-100 hover:shadow-md"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="18"
            height="18"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-2"
          >
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
          <span class="font-bold">View Report</span>
        </button>
        <button
          v-if="!structuredData || !structuredData.hasOwnProperty('risk_incidents')"
          @click="handleDownloadReport"
          class="action-button flex flex-1 items-center justify-center rounded-lg border border-indigo-200 bg-indigo-50 px-6 py-4 text-base text-indigo-700 shadow-sm transition duration-300 hover:bg-indigo-100 hover:shadow-md"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="18"
            height="18"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span class="font-bold">Download Report as HTML</span>
        </button>
      </div>
      <div class="mt-6">
        <button
          @click="handleStartNewSearch"
          class="action-button flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 px-6 py-3 text-base text-gray-600 shadow-sm transition duration-300 hover:bg-gray-100 hover:shadow-md"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="18"
            height="18"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-2"
          >
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span class="font-bold">Start a New Search</span>
        </button>
      </div>
    </div>

    <!-- Task panel with v-if condition -->
    <div v-if="searchStatus !== 'COMPLETED'" class="flex-grow rounded-lg bg-white p-4 shadow-md">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-medium text-gray-700">Tasks</h3>
        <button
          @click="hideCompletedTasks = !hideCompletedTasks"
          class="flex items-center justify-center rounded bg-gray-100 p-1.5 text-gray-600 transition-colors hover:bg-gray-200"
          :title="hideCompletedTasks ? 'Show all tasks' : 'Hide completed tasks'"
        >
          <!-- Eye icon when tasks are hidden (show all) -->
          <svg
            v-if="hideCompletedTasks"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
          >
            <path
              d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
            />
          </svg>
          <!-- Hide icon when all tasks are shown (hide completed) -->
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
          >
            <path
              d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM7 6h2v8H7V6zm4 0h2v8h-2V6z"
            />
          </svg>
          <span class="ml-1.5 text-xs">{{
            hideCompletedTasks ? 'Show all' : 'Hide completed'
          }}</span>
        </button>
      </div>
      <div class="mt-2">
        <div v-if="tasks.length === 0">
          <AaText>No tasks available yet. 🔍</AaText>
        </div>
        <div v-else class="space-y-1">
          <!-- Placeholder for hidden completed tasks -->
          <div
            v-if="hideCompletedTasks && completedTasksCount > 0"
            class="flex items-center border-l-2 border-green-200 py-2 pl-3"
          >
            <div class="mr-2 flex h-4 w-4 items-center justify-center rounded-full bg-green-100">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                class="h-3 w-3 text-green-600"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
              >
                <path d="M5 12l5 5L20 7" />
              </svg>
            </div>
            <AaText weight="normal" class="text-sm text-gray-500"
              >{{ completedTasksCount }}
              {{ completedTasksCount === 1 ? 'task' : 'tasks' }} completed</AaText
            >
          </div>

          <!-- Use the recursive TaskItem component for each visible task -->
          <TaskItem v-for="task in visibleTasks" :key="task.id" :task="task" />
        </div>
      </div>
    </div>

    <!-- Dummy container for better scrolling -->
    <div class="pb-50 h-[300px]"></div>
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

.bouncing-animation {
  animation: bounce 4s infinite;
  border-radius: 0.5rem; /* Match the container's rounded corners */
}

.bouncing-animation-reverse {
  animation: bounceReverse 3.5s infinite;
  border-radius: 0.5rem; /* Match the container's rounded corners */
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

@keyframes dot1 {
  0% {
    left: -10px;
    animation-timing-function: ease-in;
  }
  50% {
    left: 50%;
    animation-timing-function: ease-out;
  }
  100% {
    left: 110%;
  }
}

@keyframes dot2 {
  0% {
    left: -10px;
    animation-timing-function: ease-in;
  }
  20% {
    left: -10px;
    animation-timing-function: ease-in;
  }
  70% {
    left: 50%;
    animation-timing-function: ease-out;
  }
  100% {
    left: 110%;
  }
}

@keyframes dot3 {
  0% {
    left: -10px;
    animation-timing-function: ease-in;
  }
  40% {
    left: -10px;
    animation-timing-function: ease-in;
  }
  90% {
    left: 50%;
    animation-timing-function: ease-out;
  }
  100% {
    left: 110%;
  }
}

.animate-progress {
  animation: progress 3s linear infinite;
  width: 50%;
}

.animate-dot1 {
  animation:
    dot1 4s infinite,
    pulseDot 2s infinite;
}

.animate-dot2 {
  animation:
    dot2 4s 0.5s infinite,
    pulseDot 2s 0.7s infinite;
}

.animate-dot3 {
  animation:
    dot3 4s 1s infinite,
    pulseDot 2s 1.4s infinite;
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

.shimmer-effect {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.4) 25%,
    rgba(255, 255, 255, 0.6) 50%,
    rgba(255, 255, 255, 0.4) 75%,
    rgba(255, 255, 255, 0) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

.bubble-animation {
  animation: bubble 1.5s ease-in-out infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

.blink {
  animation: blink 1s step-end infinite;
}

.tool-result-container {
  max-height: 50px;
  position: relative;
  overflow: hidden;
}

.tool-result-content {
  white-space: pre-wrap;
  word-break: break-word;
  color: rgba(209, 213, 219, 0.6);
  font-size: 0.75rem;
  padding-bottom: 15px;
  mask-image: linear-gradient(to bottom, black 60%, transparent 90%);
  -webkit-mask-image: linear-gradient(to bottom, black 60%, transparent 90%);
}

.tool-result-ellipsis {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(209, 213, 219, 0.5);
  font-size: 14px;
  height: 15px;
  line-height: 10px;
  pointer-events: none;
}

.tool-result-fade {
  display: none;
}

@keyframes log-blink {
  0%,
  80%,
  100% {
    opacity: 1;
  }
  40% {
    opacity: 0.5;
  }
}

.log-blink-text {
  animation: log-blink 2s infinite;
}

.log-blink-container {
  position: relative;
}

.log-blink-container::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: #f59e0b;
  animation: log-blink 2s infinite;
}

@keyframes dots {
  0%,
  20% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
  60%,
  100% {
    opacity: 0;
  }
}

.log-loading .dot-1 {
  animation: dots 1.5s infinite;
  animation-delay: 0s;
}

.log-loading .dot-2 {
  animation: dots 1.5s infinite;
  animation-delay: 0.3s;
}

.log-loading .dot-3 {
  animation: dots 1.5s infinite;
  animation-delay: 0.6s;
}

.text-thinking-blink {
  color: #d1d5db;
  animation: thinking-blink 2s ease-in-out infinite;
}

@keyframes thinking-blink {
  0%,
  100% {
    opacity: 0.9;
  }
  50% {
    opacity: 0.5;
  }
}

.thinking-pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #60a5fa;
  animation: thinking-pulse 1.5s ease-in-out infinite;
  vertical-align: middle;
}

@keyframes thinking-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 rgba(96, 165, 250, 0);
  }
  50% {
    transform: scale(1.3);
    box-shadow: 0 0 8px rgba(96, 165, 250, 0.7);
  }
}

/* Force scrollbars to be visible at all times with strong styling */
.research-data-panel {
  overflow-y: scroll !important;
  -ms-overflow-style: scrollbar !important; /* For IE and Edge */
  scrollbar-width: auto !important; /* For Firefox */
  scrollbar-color: rgba(156, 163, 175, 0.8) rgba(241, 241, 241, 0.8) !important; /* For Firefox */
}

.terminal-panel {
  overflow-y: scroll !important;
  -ms-overflow-style: scrollbar !important; /* For IE and Edge */
  scrollbar-width: auto !important; /* For Firefox */
  scrollbar-color: rgba(75, 85, 99, 0.8) rgba(55, 65, 81, 0.8) !important; /* For Firefox */
}

/* WebKit (Chrome, Safari, newer Edge) scrollbar styling with strong contrast */
.research-data-panel::-webkit-scrollbar {
  -webkit-appearance: none !important;
  width: 12px !important;
  height: 12px !important;
  background-color: rgba(241, 241, 241, 0.8) !important;
  border-radius: 0 !important;
  border: none !important;
}

.research-data-panel::-webkit-scrollbar-thumb {
  -webkit-appearance: none !important;
  border: 3px solid rgba(241, 241, 241, 0.8) !important;
  background-color: rgba(156, 163, 175, 0.8) !important;
  border-radius: 8px !important;
}

.terminal-panel::-webkit-scrollbar {
  -webkit-appearance: none !important;
  width: 12px !important;
  height: 12px !important;
  background-color: rgba(55, 65, 81, 0.8) !important;
  border-radius: 0 !important;
  border: none !important;
}

.terminal-panel::-webkit-scrollbar-thumb {
  -webkit-appearance: none !important;
  border: 3px solid rgba(55, 65, 81, 0.8) !important;
  background-color: rgba(75, 85, 99, 0.8) !important;
  border-radius: 8px !important;
}

/* Remove the nested container scrollbars - let the parent handle scrolling */
.structured-data-container,
.extracted-text-container {
  overflow: visible !important;
  height: auto !important;
}

/* Action buttons styles - fix layout issues */
.action-buttons {
  min-height: 400px; /* Increased height */
  transition: all 0.3s ease-in-out;
  padding-top: 3rem;
  padding-bottom: 3rem;
}

.action-button {
  position: relative;
  overflow: hidden;
}

.action-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: all 0.6s;
}

.action-button:hover::after {
  left: 100%;
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

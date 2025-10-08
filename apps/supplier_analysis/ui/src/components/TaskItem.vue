<script lang="ts">
// Import the Task interface from WorkCompanySearch
import type { Task } from '../composables/useTaskProgress';
import { AaText } from '@aleph-alpha/ds-components-vue';
// Import the AaText component
import { defineComponent, computed } from 'vue';
import type { PropType } from 'vue';

export default defineComponent({
  name: 'TaskItem', // Name for recursive component
  components: {
    AaText,
  },
  props: {
    task: {
      type: Object as PropType<Task>,
      required: true,
    },
  },
  setup(props) {
    const borderColorClass = computed(() => {
      switch (props.task.status) {
        case 'COMPLETED':
          return 'border-green-300';
        case 'IN_PROGRESS':
          return 'border-yellow-300';
        case 'FAILED':
          return 'border-red-300';
        default:
          return 'border-gray-200';
      }
    });

    return {
      borderColorClass,
    };
  },
});
</script>

<template>
  <div class="task-item py-1" :class="{ 'task-in-progress': task.status === 'IN_PROGRESS' }">
    <!-- Status indicator and description in one compact line -->
    <div class="flex items-center">
      <div
        class="status-indicator mr-2 flex h-4 w-4 items-center justify-center rounded-full"
        :class="{
          'bg-green-100': task.status === 'COMPLETED',
          'task-status-blink bg-yellow-500': task.status === 'IN_PROGRESS',
          'bg-red-500': task.status === 'FAILED',
          'bg-gray-300': task.status === 'PENDING',
        }"
      >
        <svg
          v-if="task.status === 'COMPLETED'"
          class="h-3 w-3 text-green-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
        <svg
          v-else-if="task.status === 'IN_PROGRESS'"
          class="pulse-icon h-3 w-3 text-white"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
        <svg
          v-else-if="task.status === 'FAILED'"
          class="h-3 w-3 text-white"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>
      <AaText
        :weight="task.status === 'IN_PROGRESS' ? 'semibold' : 'normal'"
        class="text-sm"
        :class="{
          'text-gray-500': task.status === 'COMPLETED',
          'text-black': task.status !== 'COMPLETED' && task.status !== 'IN_PROGRESS',
          'task-text-blink': task.status === 'IN_PROGRESS',
        }"
      >
        {{ task.description }}
      </AaText>
    </div>

    <!-- Subtasks with minimal indentation -->
    <div v-if="task.subtasks && task.subtasks.length > 0" class="ml-4 mt-0.5">
      <TaskItem v-for="subtask in task.subtasks" :key="subtask.id" :task="subtask" />
    </div>
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
    left: calc(100% - 48px);
  }
}

@keyframes bounceReverse {
  0%,
  100% {
    right: 0;
    animation-timing-function: ease-in-out;
  }
  50% {
    right: calc(100% - 40px);
  }
}

.bouncing-animation {
  animation: bounce 8s infinite;
  border-radius: 0.2rem;
  height: 15px !important;
}

.bouncing-animation-reverse {
  animation: bounceReverse 8s infinite;
  border-radius: 1rem;
}

/* Style for subtasks */
.subtask {
  padding: 0.25rem;
  font-size: 0.8125rem;
}

.subtask .bouncing-animation {
  width: 8px;
  height: 1.5px;
}

@keyframes task-pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
    box-shadow: 0 0 0 rgba(234, 179, 8, 0);
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
    box-shadow: 0 0 8px rgba(234, 179, 8, 0.6);
  }
}

.task-status-blink {
  animation: task-pulse 1.5s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.3);
  }
}

.pulse-icon {
  animation: pulse-icon 1.5s ease-in-out infinite;
}

@keyframes task-text-blink {
  0%,
  100% {
    color: rgba(0, 0, 0, 0.9);
  }
  50% {
    color: rgba(107, 114, 128, 0.9);
  }
}

.task-text-blink {
  animation: task-text-blink 2s ease-in-out infinite;
  font-weight: bold;
}

.task-in-progress {
  position: relative;
}

.task-in-progress::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 12px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: #eab308;
  animation: task-pulse 1.5s ease-in-out infinite;
}
</style>

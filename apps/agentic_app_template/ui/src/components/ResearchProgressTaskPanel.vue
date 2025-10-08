<script setup lang="ts">
import type { Task } from '../composables/useTaskProgress';
import TaskItem from './ResearchProgressTaskItem.vue';
import { AaText, AaButton, AaInfoBadge } from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

const props = defineProps<{
  tasks: Task[];
  searchStatus: string | null;
}>();

const hideCompletedTasks = ref(true);

const countCompletedTasks = (taskList: Task[]): number => {
  let count = 0;
  for (const task of taskList) {
    if (task.status === 'COMPLETED') count++;
    if (task.subtasks) count += countCompletedTasks(task.subtasks);
  }
  return count;
};

const filterCompletedTasks = (taskList: Task[]): Task[] =>
  taskList
    .filter((task) => task.status !== 'COMPLETED')
    .map((task) =>
      task.subtasks && task.subtasks.length > 0
        ? { ...task, subtasks: filterCompletedTasks(task.subtasks) }
        : task
    );

const visibleTasks = computed(() =>
  !hideCompletedTasks.value ? props.tasks : filterCompletedTasks(props.tasks)
);
const completedTasksCount = computed(() => countCompletedTasks(props.tasks));
</script>

<template>
  <div v-if="searchStatus !== 'COMPLETED'" class="w-full rounded-lg bg-white p-4 shadow-md">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-sm font-medium text-gray-700">Tasks</h3>
      <AaButton
        @click="hideCompletedTasks = !hideCompletedTasks"
        variant="text"
        size="small"
        :prepend-icon="
          hideCompletedTasks ? 'i-material-symbols-visibility' : 'i-material-symbols-visibility-off'
        "
        :title="hideCompletedTasks ? 'Show all tasks' : 'Hide completed tasks'"
      >
        {{ hideCompletedTasks ? 'Show all' : 'Hide completed' }}
      </AaButton>
    </div>
    <div class="space-y-2">
      <div v-if="tasks.length === 0">
        <AaText>No tasks available yet. 🔍</AaText>
      </div>
      <div v-else class="space-y-2">
        <!-- Placeholder for hidden completed tasks -->
        <div
          v-if="hideCompletedTasks && completedTasksCount > 0"
          class="flex items-center border-l-2 border-green-200 py-2 pl-3"
        >
          <AaInfoBadge
            :soft="true"
            variant="success"
            prepend-icon="i-material-symbols-check"
            class="mr-2"
          >
            {{ completedTasksCount }} {{ completedTasksCount === 1 ? 'task' : 'tasks' }} completed
          </AaInfoBadge>
        </div>

        <!-- Use the recursive ResearchProgressTaskItem component for each visible task -->
        <TaskItem v-for="task in visibleTasks" :key="task.id" :task="task" />
      </div>
    </div>
  </div>
</template>

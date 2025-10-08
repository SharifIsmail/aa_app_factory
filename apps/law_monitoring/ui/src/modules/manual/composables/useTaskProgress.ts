import { type Ref, ref, watch } from 'vue';

export interface Task {
  id: string;
  description: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' | 'FAILED';
  subtasks?: Task[];
}

export function useTaskProgress(tasks: Ref<Task[]>, searchStatus: Ref<string | null>) {
  const progressPercentage = ref(0);
  const taskCounter = ref('0/0');
  const currentTask = ref<Task | null>(null);

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

  const countTotalTasks = (taskList: Task[]): number => {
    let count = taskList.length;
    for (const task of taskList) {
      if (task.subtasks) {
        count += countTotalTasks(task.subtasks);
      }
    }
    return count;
  };

  const findInProgressTask = (taskList: Task[] | undefined): Task | null => {
    if (!taskList) return null;

    for (const task of taskList) {
      if (task.status === 'IN_PROGRESS') {
        return task;
      }
      if (task.subtasks) {
        const inProgressSubtask = findInProgressTask(task.subtasks);
        if (inProgressSubtask) {
          return inProgressSubtask;
        }
      }
    }
    return null;
  };

  watch(
    [tasks, searchStatus],
    () => {
      // Find current in-progress task
      currentTask.value = findInProgressTask(tasks.value);

      // Calculate progress
      const totalTasks = countTotalTasks(tasks.value);
      const completedTasks = countCompletedTasks(tasks.value);
      taskCounter.value = `${completedTasks}/${totalTasks}`;

      progressPercentage.value =
        totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    },
    { immediate: true }
  );

  return {
    progressPercentage,
    taskCounter,
    currentTask,
  };
}

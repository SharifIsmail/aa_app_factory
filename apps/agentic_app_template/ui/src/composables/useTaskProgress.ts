import { type Ref, ref, watch } from 'vue';

export interface Task {
  id: string;
  description: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' | 'FAILED';
  subtasks?: Task[];
}

export function useTaskProgress(
  tasks: Ref<Task[]>,
  currentTask: Ref<Task | null>,
  searchStatus: Ref<string | null>
) {
  const progressPercentage = ref(0);
  const taskCounter = ref('0/0');

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

  watch(
    [tasks, currentTask, searchStatus],
    () => {
      const totalTasks = countTotalTasks(tasks.value);
      const completedTasks = countCompletedTasks(tasks.value);
      taskCounter.value = `${completedTasks}/${totalTasks} Tasks`;

      progressPercentage.value =
        totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    },
    { immediate: true }
  );

  return {
    progressPercentage,
    taskCounter,
  };
}

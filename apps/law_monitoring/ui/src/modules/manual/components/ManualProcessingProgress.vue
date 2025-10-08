<script setup lang="ts">
import { type Task } from '@/modules/manual/composables/useTaskProgress.ts';
import { AaIconButton, AaText, AaProgressBarLoading } from '@aleph-alpha/ds-components-vue';

interface Props {
  progressPercentage: number;
  taskCounter: string;
  currentTask?: Task | null;
}

interface Emits {
  (e: 'stop-search'): void;
}

const props = withDefaults(defineProps<Props>(), {
  currentTask: null,
});

const emit = defineEmits<Emits>();

const handleStop = () => {
  emit('stop-search');
};
</script>

<template>
  <div class="mt-6">
    <div class="mb-2 flex flex-row items-center">
      <div class="flex-grow overflow-hidden">
        <AaText v-if="props.currentTask" size="sm" class="text-core-content-primary truncate">
          {{ props.currentTask.description }}
        </AaText>
        <AaText v-else size="sm" class="text-core-content-secondary">
          Loading job status...
        </AaText>
      </div>
      <AaIconButton
        @click="handleStop"
        icon="i-material-symbols-stop"
        label="Stop current task"
        aria-label="Stop current task"
      />
    </div>

    <AaProgressBarLoading :model-value="props.progressPercentage" state="processing" />
  </div>
</template>

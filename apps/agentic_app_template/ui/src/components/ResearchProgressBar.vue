<script setup lang="ts">
import type { Task } from '@/composables/useTaskProgress.ts';
import { AaText, AaIconButton, AaInfoBadge } from '@aleph-alpha/ds-components-vue';

defineProps<{
  searchStatus: string | null;
  taskCounter: string;
  currentTask: Task | null;
  progressPercentage: number;
}>();

const emit = defineEmits<{
  (e: 'stop-search'): void;
}>();

const stopSearch = () => {
  emit('stop-search');
};
</script>

<template>
  <div v-if="searchStatus !== 'COMPLETED'" class="w-full">
    <div class="flex items-start gap-3">
      <div class="flex flex-grow flex-col overflow-hidden rounded-lg bg-white shadow-md">
        <div class="flex flex-row items-center p-4 pb-2">
          <AaInfoBadge :soft="true" variant="neutral" class="mr-3" prepend-icon="">
            {{ taskCounter }}
          </AaInfoBadge>
          <div class="flex-grow overflow-hidden">
            <div v-if="currentTask" class="truncate">
              <AaText weight="normal" class="text-sm">{{ currentTask.description }}</AaText>
            </div>
            <AaText weight="" v-else class="text-sm">Loading job status...</AaText>
          </div>
          <AaIconButton
            @click="stopSearch"
            label="Stop"
            tooltip-text="Stop the research"
            icon="i-material-symbols-stop"
          />
        </div>

        <div class="flex items-center px-4 pb-4">
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
  </div>
</template>

<style scoped>
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
</style>

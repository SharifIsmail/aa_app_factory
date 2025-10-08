<script setup lang="ts">
import { useDataPreparationStore } from '@/stores/useDataPreparationStore';
import { AaText } from '@aleph-alpha/ds-components-vue';
import { onMounted, onUnmounted } from 'vue';

const dataPreparationStore = useDataPreparationStore();

onMounted(() => {
  dataPreparationStore.startPolling();
});

onUnmounted(() => {
  dataPreparationStore.stopPolling();
});
</script>

<template>
  <Transition name="fade">
    <div
      v-if="dataPreparationStore.isOverlayVisible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
    >
      <div class="rounded-lg bg-white p-8 shadow-xl">
        <div class="flex flex-col items-center space-y-4">
          <div
            v-if="dataPreparationStore.status === 'in_progress'"
            class="i-lucide-loader-circle animate-spin text-5xl text-blue-600"
          />

          <div
            v-else-if="dataPreparationStore.status === 'failed'"
            class="i-lucide-alert-circle text-5xl text-red-600"
          />
          <AaText class="text-center" size="lg" weight="medium">
            {{
              dataPreparationStore.status === 'in_progress'
                ? 'Daten werden vorbereitet'
                : 'Datenvorbereitung fehlgeschlagen'
            }}
          </AaText>
          <AaText
            v-if="dataPreparationStore.status === 'in_progress'"
            class="text-content-primary max-w-md text-center"
            size="sm"
          >
            Dies kann bis zu 15 Minuten dauern. Bitte warten...
          </AaText>
          <AaText
            v-if="dataPreparationStore.error"
            class="max-w-md text-center text-red-600"
            size="sm"
          >
            {{ dataPreparationStore.error }}
          </AaText>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

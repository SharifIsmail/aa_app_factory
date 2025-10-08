<script setup lang="ts">
import AnalysisTab from './AnalysisTab.vue';
import DataSourcesTab from './DataSourcesTab.vue';
import OverviewTab from './OverviewTab.vue';
import { AaModal, AaToggleButtons, AaButton } from '@aleph-alpha/ds-components-vue';
import { ref, computed } from 'vue';

defineOptions({
  name: 'HowThisWorks',
});

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const tabs = ref([
  { value: 'overview', label: 'Overview' },
  { value: 'analysis', label: 'Analysis Process' },
  { value: 'data', label: 'Data Sources' },
]);

const activeTab = ref(tabs.value[0].value);

const getNextTab = () => {
  const currentIndex = tabs.value.findIndex((tab) => tab.value === activeTab.value);
  if (currentIndex === -1 || currentIndex === tabs.value.length - 1) return undefined;
  return tabs.value[currentIndex + 1];
};

const getPreviousTab = () => {
  const currentIndex = tabs.value.findIndex((tab) => tab.value === activeTab.value);
  if (currentIndex === -1 || currentIndex === 0) return undefined;
  return tabs.value[currentIndex - 1];
};

const justifyClass = computed(() => {
  const prev = getPreviousTab();
  const next = getNextTab();
  return prev && next ? 'justify-between' : prev ? 'justify-start' : 'justify-end';
});
</script>

<template>
  <Teleport to="body">
    <AaModal title="How This Works" with-overlay @close="emit('close')">
      <div class="flex h-[70vh] w-[80vw] max-w-5xl flex-col overflow-hidden">
        <div class="flex gap-2 px-6 py-3">
          <AaToggleButtons v-model="activeTab" :options="tabs" />
        </div>

        <div class="tab-content text-core-content-secondary flex-1 overflow-y-auto p-6">
          <OverviewTab v-if="activeTab === 'overview'" />
          <AnalysisTab v-if="activeTab === 'analysis'" />
          <DataSourcesTab v-if="activeTab === 'data'" />
        </div>
      </div>

      <template #footer>
        <div :class="['flex w-full', justifyClass]">
          <AaButton
            v-if="getPreviousTab()"
            @click="activeTab = getPreviousTab()!.value"
            variant="outline"
            size="medium"
            prepend-icon="i-material-symbols-arrow-back"
          >
            Back: {{ getPreviousTab()!.label }}
          </AaButton>
          <AaButton
            v-if="getNextTab()"
            @click="activeTab = getNextTab()!.value"
            variant="secondary"
            size="medium"
            append-icon="i-material-symbols-arrow-forward"
          >
            Next: {{ getNextTab()!.label }}
          </AaButton>
        </div>
      </template>
    </AaModal>
  </Teleport>
</template>

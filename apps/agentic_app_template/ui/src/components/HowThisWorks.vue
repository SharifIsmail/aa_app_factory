<script setup lang="ts">
import HowThisWorksPage from './HowThisWorksPage.vue';
import { AaModal, AaToggleButtons } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

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
</script>

<template>
  <Teleport to="body">
    <AaModal title="How This Works" with-overlay @close="emit('close')">
      <div class="flex w-[900px] flex-col overflow-hidden">
        <div class="flex gap-2 px-6 py-3">
          <AaToggleButtons v-model="activeTab" :options="tabs" />
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="tab-content">
            <HowThisWorksPage
              v-if="activeTab === 'overview'"
              wrapper-class="space-y-4"
              :next="getNextTab()"
              @navigate="(section) => (activeTab = section)"
            >
              <h2 class="mb-4 text-xl font-semibold text-gray-800">Overview</h2>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
              incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
              exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </HowThisWorksPage>

            <HowThisWorksPage
              v-if="activeTab === 'analysis'"
              wrapper-class="space-y-8"
              :prev="getPreviousTab()"
              :next="getNextTab()"
              @navigate="(section) => (activeTab = section)"
            >
              <h3 class="mb-4 text-xl font-semibold text-gray-800">Analysis Process</h3>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
              incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
              exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </HowThisWorksPage>

            <HowThisWorksPage
              v-if="activeTab === 'data'"
              wrapper-class="space-y-6"
              :prev="getPreviousTab()"
              :next="getNextTab()"
              @navigate="(section) => (activeTab = section)"
            >
              <h3 class="mb-4 text-xl font-semibold text-gray-800">Data Sources</h3>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
              incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
              exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </HowThisWorksPage>
          </div>
        </div>
      </div>
    </AaModal>
  </Teleport>
</template>

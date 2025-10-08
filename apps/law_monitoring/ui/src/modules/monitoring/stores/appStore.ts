import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { MonitoringTab } from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAppStore = defineStore(createStoreId('app'), () => {
  const activeTab = ref(MonitoringTab.DASHBOARD);

  function setActiveTab(tabName: MonitoringTab) {
    activeTab.value = tabName;
  }
  return {
    activeTab,
    setActiveTab,
  };
});

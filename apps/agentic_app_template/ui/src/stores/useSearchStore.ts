import { createStoreId } from '@/stores/createStoreId.ts';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useSearchStore = defineStore(
  createStoreId('search'),
  () => {
    const searchId = ref<string | null>(null);

    const hasActiveSearch = computed(() => !!searchId.value);

    function saveSearchId(id: string) {
      searchId.value = id;
    }

    function getSearchId(): string | null {
      return searchId.value;
    }

    function clearSearchId() {
      searchId.value = null;
    }

    return {
      searchId,
      hasActiveSearch,
      saveSearchId,
      getSearchId,
      clearSearchId,
    };
  },
  {
    persist: true,
  }
);

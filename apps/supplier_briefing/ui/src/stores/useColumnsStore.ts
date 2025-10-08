import { researchAgentService } from '@/utils/http.ts';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useColumnsStore = defineStore('columns', () => {
  const columns = ref<string[]>([]);
  const isLoaded = ref(false);
  const isLoading = ref(false);

  const loadColumns = async (): Promise<void> => {
    if (isLoaded.value || isLoading.value) return;
    try {
      isLoading.value = true;
      const result = await researchAgentService.getTransactionsColumns();

      if (!Array.isArray(result)) {
        console.error(`Invalid response format: expected array of columns, got ${typeof result}`);
        columns.value = [];
        isLoaded.value = false;
        return;
      }

      columns.value = result;
      isLoaded.value = true;
    } catch (error) {
      console.error((error as Error).message ?? 'Failed to load columns');
      columns.value = [];
      isLoaded.value = false;
    } finally {
      isLoading.value = false;
    }
  };

  return {
    columns,
    isLoaded,
    isLoading,
    loadColumns,
  };
});

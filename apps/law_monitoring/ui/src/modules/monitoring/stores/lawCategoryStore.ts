import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { useLawDataStore } from '@/modules/monitoring/stores/lawDataStore.ts';
import { Category } from '@/modules/monitoring/types';
import { defineStore } from 'pinia';
import { computed } from 'vue';

export const useLawCategoryStore = defineStore(createStoreId('law-category'), () => {
  const dataStore = useLawDataStore();
  const notificationStore = useNotificationStore();

  const isCategoryLoading = computed(() => (lawId: string) => {
    return dataStore.categoryUpdateLoading.includes(lawId);
  });

  // ===== CATEGORY UPDATE WITH OPTIMISTIC UI =====
  async function updateLawCategory(
    lawId: string,
    category: Category,
    optimisticUpdateCallback: (lawId: string, category: Category) => void,
    rollbackCallback: (lawId: string, originalCategory: Category) => void,
    getCurrentCategory: (lawId: string) => Category | undefined
  ): Promise<void> {
    // Get original category for potential rollback
    const originalCategory = getCurrentCategory(lawId) || Category.OPEN;

    try {
      // Apply optimistic update immediately
      optimisticUpdateCallback(lawId, category);

      await dataStore.updateLawCategory(lawId, category);
    } catch (error) {
      console.error('Failed to update law category:', error);

      // Rollback optimistic update
      rollbackCallback(lawId, originalCategory);

      notificationStore.addErrorNotification('Failed to update the category. Please try again.');
    }
  }

  return {
    isCategoryLoading,
    updateLawCategory,
  };
});

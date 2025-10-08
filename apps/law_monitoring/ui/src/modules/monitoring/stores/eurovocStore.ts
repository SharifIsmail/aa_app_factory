import { createStoreId } from '@/@core/stores/createStoreId.ts';
import { useNotificationStore } from '@/@core/stores/useNotificationStore.ts';
import { preprocessedLawService } from '@/@core/utils/http.ts';
import { withLoader } from '@/@core/utils/lawStoreHelpers.ts';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useEurovocStore = defineStore(createStoreId('eurovoc'), () => {
  const notificationStore = useNotificationStore();

  // ===== EUROVOC DESCRIPTORS STATE =====
  const eurovocDescriptors = ref<string[]>([]);
  const isLoadingDescriptors = ref(false);

  // ===== EUROVOC DESCRIPTORS MANAGEMENT =====
  async function fetchEurovocDescriptors(): Promise<string[]> {
    // Return cached data if available
    if (eurovocDescriptors.value.length > 0) {
      return eurovocDescriptors.value;
    }

    return withLoader(isLoadingDescriptors, async () => {
      try {
        const descriptors = await preprocessedLawService.getAllEurovocDescriptors();
        eurovocDescriptors.value = descriptors;
        return descriptors;
      } catch (err: any) {
        notificationStore.addErrorNotification(
          'Failed to load Eurovoc descriptors. Please try again later.'
        );
        console.error('Error fetching Eurovoc descriptors:', err);
        return [];
      }
    });
  }

  // ===== UTILITY METHODS =====
  function clearDescriptors(): void {
    eurovocDescriptors.value = [];
  }

  function hasDescriptors(): boolean {
    return eurovocDescriptors.value.length > 0;
  }

  return {
    // State
    eurovocDescriptors,
    isLoadingDescriptors,

    // Actions
    fetchEurovocDescriptors,
    clearDescriptors,

    // Getters
    hasDescriptors,
  };
});

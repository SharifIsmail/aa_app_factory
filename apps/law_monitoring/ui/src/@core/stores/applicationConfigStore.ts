import { createStoreId } from '@/@core/stores/createStoreId';
import { useNotificationStore } from '@/@core/stores/useNotificationStore';
import type { ApplicationConfig } from '@/@core/types/applicationConfig';
import { applicationConfigService } from '@/@core/utils/http';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useApplicationConfigStore = defineStore(createStoreId('application-config'), () => {
  const notificationStore = useNotificationStore();

  const applicationConfig = ref<ApplicationConfig>({
    enable_engage_partner_button: false,
  });

  const isLoading = ref(false);

  async function fetchApplicationConfig(): Promise<void> {
    try {
      isLoading.value = true;
      const config = await applicationConfigService.getApplicationConfig();
      applicationConfig.value.enable_engage_partner_button = config.enable_engage_partner_button;
    } catch (error) {
      console.error('Failed to fetch application configuration:', error);
      notificationStore.addErrorNotification(
        'Failed to load application configuration. Please try again.'
      );
    } finally {
      isLoading.value = false;
    }
  }

  return {
    applicationConfig,
    isLoading,
    fetchApplicationConfig,
  };
});

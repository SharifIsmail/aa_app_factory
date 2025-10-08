<i18n src="src/locales/locales.json" />

<script lang="ts" setup>
import AppTitleBar from '@/components/AppTitleBar.vue';
import DataPreparationOverlay from '@/components/DataPreparationOverlay.vue';
import ResearchHome from '@/components/ResearchHome.vue';
import { useColumnsStore } from '@/stores/useColumnsStore';
import { HTTP_CLIENT } from '@/utils/http.ts';
import { AppContainer } from '@app-factory/shared-frontend/components';
import { useContainerHeight } from '@app-factory/shared-frontend/composables';
import { ref, computed, onMounted } from 'vue';

const props = withDefaults(
  defineProps<{
    userToken: string;
    serviceBaseUrl?: string;
  }>(),
  {
    userToken: import.meta.env.VITE_USER_TOKEN || '',
    serviceBaseUrl: import.meta.env.VITE_SERVICE_BASE_URL || 'http://localhost:8080',
  }
);

HTTP_CLIENT.updateConfig({ baseURL: props.serviceBaseUrl, timeout: 60_000 });
HTTP_CLIENT.setBearerToken(props.userToken);

if (props.userToken == '') {
  console.warn(
    'No user token set for the application. If you launched the app locally, please set the VITE_USER_TOKEN environment variable as a valid Pharia AI token.'
  );
}

// Component refs
const appContainerRef = ref<InstanceType<typeof AppContainer>>();
const titleBarRef = ref<HTMLElement>();

// Create a computed ref for the container
const containerRef = computed(() => appContainerRef.value?.containerRef);

// Use container height composable
const { calculatedHeight } = useContainerHeight({
  containerRef,
  titleBarRef,
});

const columnsStore = useColumnsStore();
onMounted(() => {
  void columnsStore.loadColumns();
});
</script>

<template>
  <AppContainer ref="appContainerRef">
    <template #title>
      <div ref="titleBarRef"><AppTitleBar /></div>
    </template>
    <template #default> <ResearchHome :height="calculatedHeight" /> </template>
  </AppContainer>
  <DataPreparationOverlay />
</template>

<style lang="scss">
:root {
  font-family: Raleway, sans-serif, ui-sans-serif;
}
</style>

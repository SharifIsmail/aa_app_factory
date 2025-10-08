<i18n src="src/locales/locales.json" />
<script lang="ts" setup>
import AppTitleBar from '@/@core/components/AppTitleBar.vue';
import SkillLayout from '@/@core/components/SkillLayout.vue';
import { useContainerHeight } from '@/@core/composables';
import { useApplicationConfigStore } from '@/@core/stores/applicationConfigStore';
import { HTTP_CLIENT } from '@/@core/utils/http.ts';
import MonitoringHome from '@/modules/monitoring/components/MonitoringHome.vue';
import { onMounted, ref, computed } from 'vue';

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
const skillLayoutRef = ref<InstanceType<typeof SkillLayout>>();
const titleBarRef = ref<HTMLElement>();

// Create a computed ref for the container
const containerRef = computed(() => skillLayoutRef.value?.containerRef);

// Use container height composable
const { calculatedHeight } = useContainerHeight({
  containerRef,
  titleBarRef,
});

// Load application config globally
const applicationConfigStore = useApplicationConfigStore();
// Initialize data
onMounted(async () => {
  await applicationConfigStore.fetchApplicationConfig();
});
</script>

<template>
  <SkillLayout ref="skillLayoutRef">
    <template #title>
      <div ref="titleBarRef">
        <AppTitleBar />
      </div>
    </template>
    <template #default>
      <MonitoringHome class="w-full" :height="calculatedHeight" />
    </template>
  </SkillLayout>
</template>

<style lang="scss">
:root {
  font-family: Raleway, sans-serif, ui-sans-serif;
}
</style>

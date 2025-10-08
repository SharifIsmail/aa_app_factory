<i18n src="src/locales/locales.json" />
<script lang="ts" setup>
import AppContainer from '@/components/AppContainer.vue';
import AppTitleBar from '@/components/AppTitleBar.vue';
import ResearchHome from '@/components/ResearchHome.vue';
import { HTTP_CLIENT } from '@/utils/http.ts';

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
</script>

<template>
  <AppContainer>
    <template #title>
      <AppTitleBar />
    </template>
    <template #default>
      <ResearchHome />
    </template>
  </AppContainer>
</template>

<style lang="scss">
:root {
  font-family: Raleway, sans-serif, ui-sans-serif;
}
</style>

<i18n src="src/locales/locales.json" />
<script lang="ts" setup>
import LkSGHomepage from '@/components/LkSGHomepage.vue';
import SkillLayout from '@/components/SkillLayout.vue';
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
    'No user token set for the application. If you launched the app locally, please set the VITE_USER_TOKEN enviornment variable as a vaild Pharia AI token.'
  );
}
</script>

<template>
  <SkillLayout>
    <template #title>
      <!-- Title removed -->
    </template>
    <template #default>
      <LkSGHomepage></LkSGHomepage>
    </template>
  </SkillLayout>
</template>

<style lang="scss">
:root {
  font-family: Raleway, sans-serif, ui-sans-serif;
}
</style>

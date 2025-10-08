<i18n src="src/locales/locales.json" />
<script setup lang="ts">
import ResearchInputWithResults from './ResearchInputWithResults.vue';

defineProps<{
  height: number;
}>();
</script>

<template>
  <ResearchInputWithResults :height="height" />
</template>

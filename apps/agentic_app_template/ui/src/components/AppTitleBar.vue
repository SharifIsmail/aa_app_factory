<script lang="ts" setup>
import ConfigureDataSources from '@/components/ConfigureDataSources.vue';
import HowThisWorks from '@/components/HowThisWorks.vue';
import { AaButton, AaText } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

const showConfigureModal = ref(false);
const showHowThisWorksModal = ref(false);
</script>

<template>
  <div class="flex w-full items-center gap-6">
    <AaText element="h2" class="text-core-content-primary" size="sm" weight="bold">
      Sample Agentic App
    </AaText>
    <div class="ml-auto flex gap-2">
      <AaButton
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-settings"
        @click="showConfigureModal = true"
      >
        Configure Data Sources
      </AaButton>
      <AaButton
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-help"
        @click="showHowThisWorksModal = true"
      >
        How this works?
      </AaButton>
    </div>
    <ConfigureDataSources v-if="showConfigureModal" @close="showConfigureModal = false" />
    <HowThisWorks v-if="showHowThisWorksModal" @close="showHowThisWorksModal = false" />
  </div>
</template>

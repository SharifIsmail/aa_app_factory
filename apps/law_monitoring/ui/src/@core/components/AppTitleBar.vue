<script lang="ts" setup>
import CompanyConfigModal from '@/@core/components/CompanyConfigModal.vue';
import ConfigureDataSources from '@/@core/components/ConfigureDataSources.vue';
import HowThisWorks from '@/@core/components/HowThisWorks/index.vue';
import ManualHome from '@/modules/manual/components/ManualHome.vue';
import { AaButton, AaText } from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

const showConfigureModal = ref(false);
const showHowThisWorksModal = ref(false);
const showCompanyConfigModal = ref(false);
</script>

<template>
  <div class="px-XL py-L flex items-center gap-6">
    <AaText element="h1" class="text-core-content-primary" size="sm" weight="bold">
      EU Legal Act Monitoring
    </AaText>
    <div class="ml-auto flex gap-2">
      <AaButton
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-settings"
        @click="showCompanyConfigModal = true"
      >
        Company Settings
      </AaButton>
      <AaButton
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-help"
        @click="showHowThisWorksModal = true"
      >
        How this works?
      </AaButton>
      <ManualHome />
    </div>
    <ConfigureDataSources v-if="showConfigureModal" @close="showConfigureModal = false" />
    <CompanyConfigModal v-if="showCompanyConfigModal" @close="showCompanyConfigModal = false" />
    <HowThisWorks v-if="showHowThisWorksModal" @close="showHowThisWorksModal = false" />
  </div>
</template>

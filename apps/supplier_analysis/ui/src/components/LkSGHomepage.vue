<i18n src="src/locales/locales.json" />
<script setup lang="ts">
import ConfigureDataSources from './ConfigureDataSources.vue';
import HowThisWorks from './HowThisWorks.vue';
import InputCompanySearch from './InputCompanySearch.vue';
import WorkCompanySearch from './WorkCompanySearch.vue';
import { storageUtils } from '@/utils/storage';
import { AaText } from '@aleph-alpha/ds-components-vue';
import { ref, onMounted } from 'vue';

const searchId = ref<string | null>(null);
const isRisks = ref(false);
const showSearchInput = ref(true);
const showConfigurePopup = ref(false);
const showHowThisWorksPopup = ref(false);

onMounted(() => {
  // Check if there's an active search in localStorage
  const savedSearchId = storageUtils.getSearchId();
  if (savedSearchId) {
    console.log('Found saved search ID in localStorage:', savedSearchId);
    searchId.value = savedSearchId;
    showSearchInput.value = false;
  } else {
    showSearchInput.value = true;
  }
});

const handleSearchStarted = (id: string, isRisksSearch: boolean = false) => {
  console.log('Search started with ID:', id);
  searchId.value = id;
  isRisks.value = isRisksSearch;
  showSearchInput.value = false;
  // Save search ID to localStorage
  storageUtils.saveSearchId(id);
};

const handleStopSearch = () => {
  console.log('Search stopped');
  searchId.value = null;
  isRisks.value = false;
  showSearchInput.value = true;
  // Clear search ID from localStorage
  storageUtils.clearSearchId();
};
</script>

<template>
  <div class="homepage-container h-full w-full flex-grow">
    <div class="menu-bar w-full border-b border-gray-200 bg-gray-100">
      <div class="mx-auto flex h-12 max-w-7xl items-center justify-between px-8">
        <AaText size="lg" weight="bold" color="text-core-content-primary"
          >Supplier Risk Analysis</AaText
        >
        <div class="flex gap-6">
          <AaText
            size="base"
            weight="medium"
            class="flex cursor-pointer items-center gap-2 rounded-md bg-gray-50 px-3 py-1 text-gray-700 transition-colors hover:bg-gray-100"
            @click="showConfigurePopup = true"
          >
            <span class="i-material-symbols-settings text-gray-700"></span>
            Configure Data Sources
          </AaText>
          <AaText
            size="base"
            weight="medium"
            class="flex cursor-pointer items-center gap-2 rounded-md bg-gray-50 px-3 py-1 text-gray-700 transition-colors hover:bg-gray-100"
            @click="showHowThisWorksPopup = true"
          >
            <span class="i-material-symbols-help text-indigo-600"></span>
            How this works?
          </AaText>
        </div>
      </div>
    </div>

    <ConfigureDataSources v-if="showConfigurePopup" @close="showConfigurePopup = false" />

    <HowThisWorks v-if="showHowThisWorksPopup" @close="showHowThisWorksPopup = false" />

    <div class="scrollable-content px-[60px] py-6">
      <!-- Show company search form when on input screen -->
      <div v-if="showSearchInput">
        <!-- Company Search Input Form -->
        <InputCompanySearch
          @search-started="handleSearchStarted"
          @risks-search-started="handleSearchStarted"
        />
      </div>

      <!-- Only show WorkCompanySearch when searchId exists -->
      <WorkCompanySearch
        v-else
        :search-id="searchId"
        :is-risks="isRisks"
        @stop-search="handleStopSearch"
      />

      <div class="h-20"></div>
      <!-- Extra space at the bottom -->
    </div>
  </div>
</template>

<style scoped>
.homepage-container {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scrollable-content {
  flex: 1;
  overflow-y: auto;
  height: calc(100vh - 3.5rem);
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}
</style>

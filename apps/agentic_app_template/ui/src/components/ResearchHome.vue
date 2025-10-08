<i18n src="src/locales/locales.json" />
<script setup lang="ts">
import ResearchInputData from './ResearchInputData.vue';
import ResearchProgress from './ResearchProgress.vue';
import { useSearchStore } from '@/stores/useSearchStore.ts';
import { ref, onMounted } from 'vue';

const searchStore = useSearchStore();
const showSearchInput = ref(true);

onMounted(() => {
  if (searchStore.hasActiveSearch) {
    console.log('Found saved search ID in localStorage:', searchStore.searchId);
    showSearchInput.value = false;
  } else {
    showSearchInput.value = true;
  }
});

const handleSearchStarted = (id: string) => {
  console.log('Search started with ID:', id);
  searchStore.saveSearchId(id);
  showSearchInput.value = false;
};

const handleStopSearch = () => {
  console.log('Search stopped');
  searchStore.clearSearchId();
  showSearchInput.value = true;
};
</script>

<template>
  <div class="homepage-container h-full w-full flex-grow">
    <div class="scrollable-content w-full px-4 py-6">
      <div v-if="showSearchInput">
        <ResearchInputData @search-started="handleSearchStarted" />
      </div>

      <!-- Only show ResearchProgress when searchId exists -->
      <ResearchProgress v-else :search-id="searchStore.searchId" @stop-search="handleStopSearch" />

      <div class="h-20"></div>
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
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}
</style>

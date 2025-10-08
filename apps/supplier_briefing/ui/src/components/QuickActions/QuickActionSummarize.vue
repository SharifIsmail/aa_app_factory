<script setup lang="ts">
import type { PartnerData } from '@/types/api';
import { researchAgentService } from '@/utils/http';
import { AaButton } from '@aleph-alpha/ds-components-vue';
import { computed, ref, watch } from 'vue';

type PartnerOption = { id: string; name: string };

const props = withDefaults(
  defineProps<{
    isDisabled: boolean;
    isSearching: boolean;
    autoOpen?: boolean;
  }>(),
  {
    autoOpen: false,
  }
);

const emit = defineEmits<{
  (e: 'click'): void;
  (e: 'partner-selected', partnerId: string | null): void;
}>();

const disabled = computed(() => props.isDisabled || props.isSearching);
const isOpen = ref<boolean>(props.autoOpen);
watch(
  () => props.autoOpen,
  (val) => {
    isOpen.value = val;
  }
);

const selectedPartnerId = ref<string | null>(null);
const searchQuery = ref('');
const isDropdownOpen = ref(false);
const searchResults = ref<PartnerOption[]>([]);
const searchError = ref<string>('');
const hasSearched = ref<boolean>(false);
const isPartnerSearching = ref<boolean>(false);

const isAnySearching = computed(() => props.isSearching || isPartnerSearching.value);

const searchStatusText = computed(() => {
  if (isPartnerSearching.value) return 'Searching, please wait...';
  if (props.isSearching) return 'Searching...';
  if (!searchQuery.value) return 'Type to search for partners';
  if (!hasSearched.value) return 'Press Search button to find partners';
  return `No partners found for "${searchQuery.value}"`;
});

const filteredPartners = computed(() => {
  return searchResults.value;
});

const selectedPartner = computed(() => {
  return searchResults.value.find((p) => p.id === selectedPartnerId.value);
});

const toggleOpen = () => {
  if (disabled.value) return;
  isOpen.value = !isOpen.value;
  emit('click');
};

const selectPartner = (partner: PartnerOption) => {
  selectedPartnerId.value = partner.id;
  isDropdownOpen.value = false;
  searchQuery.value = '';
  emit('partner-selected', partner.id);
};

const clearSelection = () => {
  selectedPartnerId.value = null;
  emit('partner-selected', null);
};

const clearSearchResults = () => {
  searchResults.value = [];
  searchError.value = '';
  hasSearched.value = false;
};

const handleSearchBlur = () => {
  setTimeout(() => {
    if (
      !props.isSearching &&
      !isPartnerSearching.value &&
      searchResults.value.length === 0 &&
      !searchError.value &&
      !hasSearched.value
    ) {
      isDropdownOpen.value = false;
    }
  }, 150);
};

const handleFilterSearch = async () => {
  if (
    props.isSearching ||
    isPartnerSearching.value ||
    !searchQuery.value.trim() ||
    searchQuery.value.trim().length < 2
  )
    return;

  isPartnerSearching.value = true;
  searchError.value = '';
  hasSearched.value = true;

  try {
    const response = await researchAgentService.filterQuickActionData<PartnerData>({
      flow_name: 'summarize_business_partner',
      filter_params: {
        query: searchQuery.value.trim(),
        limit: 10000,
      },
    });

    isDropdownOpen.value = true;

    if (response.success) {
      searchResults.value = response.data.map((partner: PartnerData) => ({
        id: partner.id,
        name: partner.name,
      }));
    } else {
      searchError.value = response.error || 'Search failed';
      searchResults.value = [];
    }
  } catch {
    searchError.value = 'Network error occurred';
    searchResults.value = [];
    isDropdownOpen.value = true;
  } finally {
    isPartnerSearching.value = false;
  }
};
</script>

<template>
  <div class="inline-flex">
    <AaButton
      :disabled="disabled"
      variant="secondary"
      class="whitespace-nowrap px-3"
      @click="toggleOpen"
    >
      Summarize Business Partner
    </AaButton>
  </div>

  <div
    v-if="isOpen"
    class="border-core-border-contrast bg-core-bg-primary/60 w-full basis-full rounded-lg border p-4 shadow-sm"
  >
    <div class="text-core-content-secondary mb-3 text-sm font-medium">Select business partner</div>

    <!-- Selected Partner Display -->
    <div
      v-if="selectedPartner"
      class="border-core-border-focus bg-core-bg-primary mb-3 flex items-center justify-between rounded-md border p-3"
    >
      <div class="flex items-center gap-2">
        <i class="i-material-symbols-check-circle text-core-content-success" />
        <span class="text-core-content-primary font-medium">{{ selectedPartner.name }}</span>
        <span class="text-core-content-secondary text-sm">(ID: {{ selectedPartner.id }})</span>
      </div>
      <button
        type="button"
        @click="clearSelection"
        class="text-core-content-secondary hover:text-core-content-primary transition-colors"
      >
        <i class="i-material-symbols-close" />
      </button>
    </div>

    <!-- Search Dropdown -->
    <div v-if="!selectedPartner" class="relative">
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search partners..."
          class="border-core-border-contrast bg-core-bg-primary text-core-content-primary placeholder-core-content-placeholder focus:border-core-border-focus w-full rounded-md border px-3 py-2 pr-24 focus:outline-none"
          @focus="isDropdownOpen = true"
          @blur="handleSearchBlur"
          @keyup.enter="handleFilterSearch"
          @input="clearSearchResults"
        />
        <div class="absolute right-1 top-1/2 -translate-y-1/2">
          <AaButton
            :disabled="disabled || isAnySearching || searchQuery.trim().length < 2"
            variant="primary"
            size="small"
            class="!h-auto !min-h-0 !px-3 !py-1 text-xs"
            @click="handleFilterSearch"
          >
            <i v-if="!isAnySearching" class="i-material-symbols-search mr-1 text-sm" />
            <i v-else class="i-material-symbols-progress-activity mr-1 animate-spin text-sm" />
            {{ isAnySearching ? 'Searching' : 'Search' }}
          </AaButton>
        </div>
      </div>

      <!-- Dropdown Options -->
      <div
        v-if="isDropdownOpen"
        class="border-core-border-contrast bg-core-bg-primary absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border shadow-lg"
      >
        <template v-if="filteredPartners.length > 0">
          <button
            v-for="partner in filteredPartners"
            :key="partner.id"
            type="button"
            class="hover:bg-core-bg-tertiary flex w-full items-center justify-between px-3 py-2 text-left"
            @click="selectPartner(partner)"
          >
            <div>
              <div class="text-core-content-primary font-medium">{{ partner.name }}</div>
              <div class="text-core-content-secondary text-sm">ID: {{ partner.id }}</div>
            </div>
            <i
              v-if="selectedPartnerId === partner.id"
              class="i-material-symbols-check text-core-content-success"
            />
          </button>
        </template>

        <!-- No Results -->
        <template v-else-if="searchError">
          <div class="p-3">
            <div class="text-core-content-error text-center text-sm">{{ searchError }}</div>
          </div>
        </template>

        <template v-else>
          <div class="p-3">
            <div class="text-core-content-secondary text-center text-sm">
              {{ searchStatusText }}
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

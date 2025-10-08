<script setup lang="ts">
import { TABLE_LAYOUT, calculateDynamicPageSize } from '@/@core/constants/tableLayout';
import type { EurovocDescriptorCount } from '@/modules/monitoring/types';
import {
  AaModal,
  AaText,
  AaInput,
  AaTable,
  AaTableRow,
  AaTableBody,
  AaTableCell,
  AaTableHeader,
  AaTableFooter,
  AaTableContainer,
  AaTableTitle,
  AaTableTitlebar,
  AaPagination,
  AaButton,
} from '@aleph-alpha/ds-components-vue';
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue';

interface Props {
  topics: EurovocDescriptorCount[];
  open: boolean;
  loading?: boolean;
  timelineFilter?: string;
  exportHandler?: () => void;
}

interface Emits {
  (e: 'update:open', value: boolean): void;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  timelineFilter: '',
  exportHandler: undefined,
});

const emit = defineEmits<Emits>();

const searchQuery = ref('');
const currentPage = ref(1);

const availableHeight = ref(0);
const dynamicPageSize = computed(() => {
  return calculateDynamicPageSize(availableHeight.value);
});

const calculateAvailableHeight = () => {
  const viewportHeight = window.innerHeight;
  availableHeight.value = viewportHeight * 0.75;
};

const filteredTopics = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.topics;
  }

  const query = searchQuery.value.toLowerCase();
  return props.topics.filter((topic) => topic.descriptor.toLowerCase().includes(query));
});

const sortedTopics = computed(() => {
  return [...filteredTopics.value].sort((a, b) => b.frequency - a.frequency);
});

const totalPages = computed(() => {
  return Math.ceil(sortedTopics.value.length / dynamicPageSize.value);
});

const paginatedTopics = computed(() => {
  const startIndex = (currentPage.value - 1) * dynamicPageSize.value;
  const endIndex = startIndex + dynamicPageSize.value;
  return sortedTopics.value.slice(startIndex, endIndex);
});

const currentPageRange = computed(() => {
  const startIndex = (currentPage.value - 1) * dynamicPageSize.value;
  const endIndex = Math.min(startIndex + dynamicPageSize.value, sortedTopics.value.length);
  return {
    start: startIndex + 1,
    end: endIndex,
    total: sortedTopics.value.length,
  };
});

const handleClose = () => {
  searchQuery.value = '';
  currentPage.value = 1;
  emit('update:open', false);
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

const handleExportToExcel = () => {
  try {
    if (props.exportHandler) {
      props.exportHandler();
    }
  } catch (error) {
    console.error('Error exporting to CSV:', error);
  }
};

watch(searchQuery, () => {
  currentPage.value = 1;
});

watch(dynamicPageSize, () => {
  const maxPage = Math.ceil(sortedTopics.value.length / dynamicPageSize.value);
  if (currentPage.value > maxPage && maxPage > 0) {
    currentPage.value = maxPage;
  }
});

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      await nextTick();
      calculateAvailableHeight();
    }
  }
);

onMounted(() => {
  calculateAvailableHeight();
});

const handleResize = () => {
  calculateAvailableHeight();
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<template>
  <Teleport to="body">
    <AaModal
      v-if="open"
      :title="`All Eurovoc Topics (${timelineFilter})`"
      with-overlay
      @close="handleClose"
    >
      <div
        class="h-[75vh] w-[85vw] max-w-5xl"
        :style="{ padding: `${TABLE_LAYOUT.MODAL_PADDING}px` }"
      >
        <AaTableContainer>
          <template #titlebar>
            <AaTableTitlebar :style="{ height: `${TABLE_LAYOUT.TITLEBAR_HEIGHT}px` }">
              <AaTableTitle>
                <AaText size="sm" class="text-core-content-secondary">
                  {{ sortedTopics.length }} topics found
                </AaText></AaTableTitle
              >
              <template #toolbar>
                <AaText
                  size="sm"
                  class="text-core-content-secondary"
                  v-if="sortedTopics.length > 0"
                >
                  Showing {{ currentPageRange.start }}-{{ currentPageRange.end }} of
                  {{ currentPageRange.total }}
                </AaText>
                <AaInput
                  v-model="searchQuery"
                  placeholder="Search topics..."
                  size="small"
                  name="search"
                  :disabled="loading"
                />
              </template>
            </AaTableTitlebar>
          </template>

          <div v-if="loading" class="flex items-center justify-center p-8">
            <div class="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
            <AaText size="sm" class="text-core-content-secondary ml-3"> Loading topics... </AaText>
          </div>

          <div
            v-else-if="sortedTopics.length === 0"
            class="flex flex-col items-center justify-center p-8"
          >
            <AaText size="sm" class="text-core-content-secondary">
              {{ searchQuery ? 'No topics match your search' : 'No topics available' }}
            </AaText>
          </div>

          <AaTable v-else>
            <AaTableHeader>
              <AaTableRow :style="{ height: `${TABLE_LAYOUT.HEADER_HEIGHT}px` }">
                <AaTableCell tag="th" class="w-16">Rank</AaTableCell>
                <AaTableCell tag="th">Eurovoc Topic</AaTableCell>
                <AaTableCell tag="th" class="w-24">Frequency</AaTableCell>
              </AaTableRow>
            </AaTableHeader>
            <AaTableBody>
              <AaTableRow
                v-for="(topic, index) in paginatedTopics"
                :key="topic.descriptor"
                :style="{ height: `${TABLE_LAYOUT.ROW_HEIGHT}px` }"
              >
                <AaTableCell class="font-medium">
                  {{ (currentPage - 1) * dynamicPageSize + index + 1 }}
                </AaTableCell>
                <AaTableCell>
                  {{ topic.descriptor }}
                </AaTableCell>
                <AaTableCell class="font-semibold">
                  {{ topic.frequency }}
                </AaTableCell>
              </AaTableRow>
            </AaTableBody>
            <AaTableFooter
              v-if="totalPages > 1"
              :style="{ height: `${TABLE_LAYOUT.FOOTER_HEIGHT}px` }"
            >
              <div class="flex justify-center">
                <AaPagination
                  :current="currentPage"
                  :total="totalPages"
                  @go-to-page="handlePageChange"
                />
              </div>
            </AaTableFooter>
          </AaTable>
        </AaTableContainer>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <AaButton variant="text" @click="handleClose">Close</AaButton>
          <AaButton
            :disabled="loading || sortedTopics.length === 0"
            prepend-icon="i-material-symbols-download"
            @click="handleExportToExcel"
            >Export to CSV</AaButton
          >
        </div>
      </template>
    </AaModal>
  </Teleport>
</template>

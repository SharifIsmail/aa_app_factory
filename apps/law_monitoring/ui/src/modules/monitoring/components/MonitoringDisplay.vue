<script setup lang="ts">
import MonitoringReportHtml from './MonitoringReportHtml.vue';
import { formatGermanDate } from '@/@core/utils/formatGermanDate.ts';
import { manualLawAnalysisService } from '@/@core/utils/http.ts';
import {
  sortLawsByDateAndStatus,
  groupLawsByDate,
  getSortedDateKeys,
} from '@/@core/utils/sortLaws.ts';
import MonitoringDisplayAccordion from '@/modules/monitoring/components/MonitoringDisplayAccordion.vue';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore.ts';
import { DisplayMode } from '@/modules/monitoring/stores/lawDisplayStore.ts';
import { AaText, AaSkeletonLoading, AaButton } from '@aleph-alpha/ds-components-vue';
import type { PreprocessedLaw } from 'src/modules/monitoring/types';
import { computed, ref } from 'vue';

const lawCoordinatorStore = useLawCoordinatorStore();

const reportComponents = ref<Record<string, InstanceType<typeof MonitoringReportHtml>>>({});

// Filter state
const activeFilter = ref<string | null>(null);

// Filtered laws based on active filter
const filteredLaws = computed(() => {
  if (!activeFilter.value) {
    return lawCoordinatorStore.displayedLaws;
  }
  return lawCoordinatorStore.displayedLaws.filter((law) => law.status === activeFilter.value);
});

// Group filtered laws by date
const groupedLawsByDate = computed(() => {
  const sortedLaws = sortLawsByDateAndStatus(filteredLaws.value);
  return groupLawsByDate(sortedLaws);
});

// Get sorted date keys
const sortedDateKeys = computed(() => {
  return getSortedDateKeys(groupedLawsByDate.value);
});

// Get laws for a specific date
const getLawsForDate = (date: string) => {
  return groupedLawsByDate.value[date] || [];
};

const openFullReport = (law: PreprocessedLaw) => {
  const reportComponent = reportComponents.value[law.law_file_id];
  if (reportComponent) {
    reportComponent.openFullReport();
  }
};

const handleShowMore = async () => {
  await lawCoordinatorStore.loadMoreDays();
};

const downloadPdfReport = async (law: PreprocessedLaw) => {
  if (!law?.law_file_id) return;

  try {
    const uuid = law.law_file_id.replace(/^law_/, ''); // Remove 'law_' prefix for backend compatibility
    const pdfContent = await manualLawAnalysisService.getReport(uuid, true, 'pdf', true);

    // Create blob and trigger download
    const blob = new Blob([pdfContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `law_report_${uuid}.pdf`;
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to download PDF report:', error);
    // Note: We could add notification here if needed, but keeping it simple for now
  }
};

const downloadWordReport = async (law: PreprocessedLaw) => {
  if (!law?.law_file_id) return;

  try {
    const uuid = law.law_file_id.replace(/^law_/, ''); // Remove 'law_' prefix for backend compatibility
    const docxContent = await manualLawAnalysisService.getReport(uuid, true, 'docx', true);

    // Create blob and trigger download
    const blob = new Blob([docxContent], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `law_report_${uuid}.docx`;
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to download Word report:', error);
    // Note: We could add notification here if needed, but keeping it simple for now
  }
};
</script>

<template>
  <div class="flex w-full flex-col py-4">
    <div v-if="lawCoordinatorStore.displayMode" class="flex h-full flex-col">
      <div
        v-if="
          (lawCoordinatorStore.isLoading ||
            lawCoordinatorStore.isSearching ||
            lawCoordinatorStore.isLoadingLawsByDate) &&
          !lawCoordinatorStore.isLoadingMore
        "
        class="p-XL space-y-2"
      >
        <div v-for="n in 6" :key="n" class="h-10 w-full">
          <AaSkeletonLoading class="rounded"></AaSkeletonLoading>
        </div>
      </div>

      <div
        v-else-if="
          !lawCoordinatorStore.displayedLaws.length &&
          lawCoordinatorStore.displayMode &&
          !lawCoordinatorStore.isLoadingDates &&
          !lawCoordinatorStore.isLoading &&
          !lawCoordinatorStore.isSearching &&
          !lawCoordinatorStore.isLoadingMore &&
          !lawCoordinatorStore.hasMoreLaws
        "
        class="text-core-content-tertiary pt-2"
      >
        No legal acts found, please try a different date or a different search term.
      </div>

      <div v-else-if="lawCoordinatorStore.displayedLaws.length > 0" class="flex flex-1 flex-col">
        <MonitoringReportHtml
          v-for="law in filteredLaws"
          :key="`report-${law.law_file_id}`"
          :law="law"
          :ref="
            (el) => {
              if (el)
                reportComponents[law.law_file_id] = el as InstanceType<typeof MonitoringReportHtml>;
            }
          "
        />

        <div class="flex-1 overflow-y-auto">
          <div v-for="date in sortedDateKeys" :key="date" class="mb-8">
            <AaText weight="bold" class="text-core-content-primary">
              {{ formatGermanDate(new Date(date)) }}
            </AaText>

            <div v-if="getLawsForDate(date).length > 0" class="pt-2">
              <MonitoringDisplayAccordion
                :key="`laws-${date}-${activeFilter || 'all'}`"
                :laws="getLawsForDate(date)"
                @open-full-report="openFullReport"
                @download-pdf-report="downloadPdfReport"
                @download-word-report="downloadWordReport"
              />
            </div>
          </div>
        </div>

        <div v-if="lawCoordinatorStore.displayMode === DisplayMode.DEFAULT" class="self-center">
          <AaButton
            v-if="lawCoordinatorStore.hasMoreLaws"
            variant="secondary"
            @click="handleShowMore"
            :loading="lawCoordinatorStore.isLoadingMore"
            :disabled="lawCoordinatorStore.isLoadingMore"
          >
            {{ lawCoordinatorStore.isLoadingMore ? 'Loading...' : 'Show Older Legal Acts' }}
          </AaButton>
          <AaText v-else class="text-core-content-tertiary py-4 text-center text-sm">
            No more legal acts available. For older legal acts, please use the manual report
            generation.
          </AaText>
        </div>
      </div>
    </div>
  </div>
</template>

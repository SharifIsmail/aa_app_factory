<script setup lang="ts">
import type { PreprocessedLaw, Citation } from '../types';
import { OfficialJournalSeries } from '../types';
import LawLabelSection from './LawLabelSection.vue';
import MonitoringLawActions from './MonitoringLawActions.vue';
import CitationButton from '@/@core/components/CitationButton.vue';
import MarkdownRenderer from '@/@core/components/MarkdownRenderer.vue';
import { formatGermanDate } from '@/@core/utils/formatGermanDate.ts';
import { getRelevantTeams } from '@/@core/utils/lawStoreHelpers.ts';
import {
  extractTextFromMarkdown,
  findSequentialMatches,
  preprocessMarkdownText,
  wrapWithMarkTag,
} from '@/@core/utils/markdownRendererUtils';
import { escapeHtml, escapeRegex, ENGLISH_STOP_WORDS } from '@/@core/utils/textUtils.ts';
import { AaText, AaModal } from '@aleph-alpha/ds-components-vue';
import { computed, ref } from 'vue';

interface Props {
  law: PreprocessedLaw;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'open-full-report': [law: PreprocessedLaw];
  'download-pdf-report': [law: PreprocessedLaw];
  'download-word-report': [law: PreprocessedLaw];
}>();

const showMetadataColumn = computed(() => {
  const hasDetails = props.law.end_validity_date || props.law.effect_date;
  const hasEurovocKeywords = props.law.eurovoc_labels && props.law.eurovoc_labels.length > 0;
  const hasDocumentType = props.law.document_type || props.law.document_type_label;
  const hasOJSeries = props.law.oj_series_label;
  return hasDetails || hasEurovocKeywords || hasDocumentType || hasOJSeries;
});

const relevantTeams = computed(() => {
  return getRelevantTeams(props.law);
});

const relevantTeamsWithFactualCitations = computed(() => {
  return relevantTeams.value.map((team) => ({
    ...team,
    factualCitations: team.citations?.filter((c) => c.factfulness.is_factual) ?? [],
  }));
});

const showCitationModal = ref(false);
const selectedCitation = ref<Citation | null>(null);

const parseBulletPoints = (text: string): string[] => {
  return text
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => line.replace(/^\*\s*/, '').trim())
    .filter((point) => point.length > 0);
};

const handleCitationClick = (citation: Citation) => {
  selectedCitation.value = citation;
  showCitationModal.value = true;
};

const closeCitationModal = () => {
  showCitationModal.value = false;
  selectedCitation.value = null;
};

const processedLawText = computed(() => {
  return preprocessMarkdownText(props.law?.law_text ?? '');
});

const processedHighlightContent = computed(() => {
  return preprocessMarkdownText(selectedCitation.value?.chunk?.content ?? '');
});

const highlightedMarkdownContent = computed(() => {
  const lawText = processedLawText.value;
  const highlightText = processedHighlightContent.value;

  if (!highlightText.trim()) {
    return lawText;
  }

  const textChunksToHighlight = extractTextFromMarkdown(highlightText);

  if (textChunksToHighlight.length === 0) {
    return lawText;
  }

  let processedText = lawText;

  // Process each chunk to find sequential matches
  textChunksToHighlight.forEach((chunk) => {
    if (chunk.length > 3) {
      const words = chunk.split(/\s+/).filter((word) => word.length > 2);

      // First try exact phrase match
      if (processedText.includes(chunk)) {
        const regex = new RegExp(`(${chunk.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        processedText = processedText.replace(regex, (match) => wrapWithMarkTag(match));
      } else {
        // Find sequential word matches in natural order
        const sequentialMatches = findSequentialMatches(processedText, words);

        // Apply highlights from right to left to avoid position shifts
        sequentialMatches.reverse().forEach((match) => {
          const before = processedText.slice(0, match.start);
          const highlighted = wrapWithMarkTag(match.text);
          const after = processedText.slice(match.end);
          processedText = before + highlighted + after;
        });
      }
    }
  });

  return processedText;
});

// Highlight Eurovoc labels within the subject matter text
const highlightedSubjectMatter = computed(() => {
  const text = props.law.subject_matter_text ?? '';
  if (!text) return '';

  const labels = (props.law.eurovoc_labels ?? []).filter(
    (l): l is string => !!l && l.trim().length > 0
  );

  const escapedText = escapeHtml(text);
  if (labels.length === 0) return escapedText;

  // Build phrase patterns first (longest first)
  const phrasePatterns = labels
    .map((l) => escapeHtml(l))
    .sort((a, b) => b.length - a.length)
    .map((l) => escapeRegex(l));

  // Build single-word token patterns from multi-word labels
  const wordTokens = Array.from(
    new Set(
      labels
        .flatMap((l) => l.split(/[^\p{L}\p{N}]+/u))
        .map((w) => w.trim())
        // Keep short tokens (e.g., AI, EU). Filter only empty strings and English stop words.
        .filter((w) => w.length > 0 && !ENGLISH_STOP_WORDS.has(w.toLowerCase()))
    )
  );

  const tokenPatterns = wordTokens
    .map((w) => escapeHtml(w))
    .map((w) => escapeRegex(w))
    .map((w) => `\\b${w}\\b`);

  const allPatterns = [...phrasePatterns, ...tokenPatterns];
  if (allPatterns.length === 0) return escapedText;

  const pattern = new RegExp(`(${allPatterns.join('|')})`, 'gi');
  return escapedText.replace(
    pattern,
    '<span class="bg-semantic-bg-warning-soft rounded-sm">$&</span>'
  );
});
</script>

<template>
  <div class="h-max-[60vh] overflow-y-auto p-4">
    <div v-if="law.status === 'PROCESSED'">
      <div class="mb-8 flex justify-between gap-8">
        <div v-if="law.subject_matter_text" class="w-7/8">
          <AaText size="base" weight="bold" class="mb-2">Subject matter</AaText>
          <p
            class="text-core-content-secondary text-sm leading-relaxed"
            v-html="highlightedSubjectMatter"
          ></p>
        </div>
        <MonitoringLawActions
          :law="law"
          class="w-1/8 flex flex-col gap-1"
          @open-full-report="emit('open-full-report', $event)"
          @download-pdf-report="emit('download-pdf-report', $event)"
          @download-word-report="emit('download-word-report', $event)"
        />
      </div>
      <div v-if="showMetadataColumn" class="align-flex-start flex gap-8">
        <div class="w-4/10 flex gap-12">
          <!-- Document Type Section -->
          <LawLabelSection
            v-if="law.document_type_label"
            title="Document Type"
            :label="law.document_type_label"
            color-class="bg-blue-100 text-blue-800"
          />

          <!-- Journal Series Section -->
          <LawLabelSection
            v-if="law.oj_series_label"
            title="Journal Series"
            :label="law.oj_series_label"
            :color-class="
              law.oj_series_label === OfficialJournalSeries.L_SERIES
                ? 'bg-green-100 text-green-800'
                : 'bg-blue-100 text-blue-800'
            "
          />

          <div v-if="law.end_validity_date || law.effect_date">
            <AaText size="base" weight="bold" class="mb-2">Details</AaText>
            <div class="flex flex-row gap-4">
              <div v-if="law.effect_date" class="text-sm">
                <span class="text-core-content-tertiary">{{ `Date of effect: ` }}</span>
                <span class="text-core-content-secondary font-bold">{{
                  formatGermanDate(law.effect_date)
                }}</span>
              </div>
              <div
                v-if="
                  law.end_validity_date && new Date(law.end_validity_date).getFullYear() !== 9999
                "
                class="text-sm"
              >
                <div>End of validity:</div>
                <div class="text-core-content-secondary">
                  {{ formatGermanDate(law.end_validity_date) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="law.eurovoc_labels && law.eurovoc_labels.length > 0" class="w-6/10">
          <AaText size="base" weight="bold" class="mb-2">Eurovoc Keywords</AaText>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="label in law.eurovoc_labels"
              :key="label"
              class="inline-block rounded-full bg-blue-100 px-3 py-1 text-xs text-blue-800"
            >
              {{ label }}
            </span>
          </div>
        </div>
      </div>
      <!-- Team Relevancy Classification Section -->
      <div v-if="relevantTeams.length > 0" class="mt-6">
        <AaText size="base" weight="bold" class="mb-3">Likely Impacted Teams</AaText>
        <div class="overflow-x-auto">
          <table class="w-full table-auto">
            <thead>
              <tr class="bg-core-bg-secondary text-core-content-primary border">
                <th class="border px-4 py-2 text-left text-sm">Team</th>
                <th class="border px-4 py-2 text-left text-sm">Reasoning</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="team in relevantTeamsWithFactualCitations" :key="team.team_name">
                <td class="text-core-content-primary border px-4 py-2 text-sm font-medium">
                  {{ team.team_name }}
                </td>
                <td class="text-core-content-secondary border px-4 py-2 text-sm">
                  <ul class="list-outside list-disc space-y-1 pl-4">
                    <li v-for="point in parseBulletPoints(team.reasoning)" :key="point">
                      <span>{{ point }}</span>
                    </li>
                  </ul>
                  <span v-if="team.factualCitations.length > 0" class="ml-1">
                    <CitationButton
                      v-for="(citation, index) in team.factualCitations"
                      :key="index"
                      class="m-1"
                      @click="handleCitationClick(citation)"
                      variant="outline"
                      prepend-icon="i-material-symbols-link"
                    >
                      {{ index + 1 }}
                    </CitationButton>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <MonitoringLawActions v-else :law="law" class="flex gap-1" />
  </div>

  <Teleport to="body">
    <AaModal
      v-if="showCitationModal"
      :show="showCitationModal"
      @close="closeCitationModal"
      with-overlay
    >
      <template #title-addon>
        <AaText size="lg" weight="bold" class="text-core-content-primary"
          >Relevancy Reasoning</AaText
        >
      </template>
      <div class="flex h-[80vh] w-[90vw] max-w-6xl flex-col overflow-hidden">
        <div class="flex-1 overflow-hidden">
          <div class="max-h-full overflow-y-auto p-4">
            <MarkdownRenderer :content="highlightedMarkdownContent" :focus-first-highlight="true" />
          </div>
        </div>
      </div>
    </AaModal>
  </Teleport>
</template>

<style scoped>
:deep(button) {
  transition: all 0.2s ease-in-out;
  cursor: pointer;
}
</style>

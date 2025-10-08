<script setup lang="ts">
import MonitoringDisplayAccordionContent from './MonitoringDisplayAccordionContent.vue';
import { formatGermanDate } from '@/@core/utils/formatGermanDate.ts';
import { getRelevantTeams } from '@/@core/utils/lawStoreHelpers.ts';
import { isLikelyRelevant } from '@/@core/utils/sortLaws.ts';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore.ts';
import { Category, type PreprocessedLaw } from '@/modules/monitoring/types';
import {
  AaText,
  AaInfoBadge,
  AaAccordion,
  AaAccordionSection,
  AaAccordionTrigger,
  AaAccordionContent,
  AaButton,
  AaTooltip,
} from '@aleph-alpha/ds-components-vue';
import { ref } from 'vue';

interface Props {
  laws: PreprocessedLaw[];
  keyPrefix?: string;
}

const props = withDefaults(defineProps<Props>(), {
  keyPrefix: '',
});

const emit = defineEmits<{
  'open-full-report': [law: PreprocessedLaw];
  'download-pdf-report': [law: PreprocessedLaw];
  'download-word-report': [law: PreprocessedLaw];
}>();

const lawCoordinatorStore = useLawCoordinatorStore();

// Create refs for tooltips
const relevantButtonRefs = ref<Record<string, HTMLElement>>({});
const notRelevantButtonRefs = ref<Record<string, HTMLElement>>({});
const relevancyBadgeRefs = ref<Record<string, HTMLElement>>({});

const getBadgeVariant = (status: string) => {
  switch (status) {
    case 'FAILED':
      return 'error';
    case 'PROCESSING':
      return 'warning';
    case 'PROCESSED':
      return 'success';
    case 'RAW':
      return 'info';
    default:
      return undefined;
  }
};

const getStatusDisplayText = (status: string) => {
  switch (status) {
    case 'RAW':
      return 'Awaiting';
    case 'PROCESSING':
      return 'Processing';
    case 'PROCESSED':
      return 'Ready';
    case 'FAILED':
      return 'Failed';
    default:
      return status;
  }
};

const handleCategoryChange = async (
  lawId: string,
  clickedCategory: Category.RELEVANT | Category.NOT_RELEVANT
) => {
  const law = props.laws.find((l) => l.law_file_id === lawId);
  if (!law) return;

  let newCategory: Category;

  // Determine the new category based on current state and clicked button
  if (clickedCategory === Category.RELEVANT) {
    // Clicking RELEVANT button
    if (law.category === Category.RELEVANT) {
      // If already RELEVANT, go to OPEN (toggle off)
      newCategory = Category.OPEN;
    } else {
      // If OPEN or NOT_RELEVANT, go to RELEVANT
      newCategory = Category.RELEVANT;
    }
  } else {
    // Clicking NOT_RELEVANT button
    if (law.category === Category.NOT_RELEVANT) {
      // If already NOT_RELEVANT, go to OPEN (toggle off)
      newCategory = Category.OPEN;
    } else {
      // If OPEN or RELEVANT, go to NOT_RELEVANT
      newCategory = Category.NOT_RELEVANT;
    }
  }

  await lawCoordinatorStore.updateLawCategory(lawId, newCategory);
};

const getSectionId = (lawId: string) => {
  return props.keyPrefix ? `${props.keyPrefix}-${lawId}` : lawId;
};

const getRelevantTooltipText = (law: PreprocessedLaw) => {
  return law.category === Category.RELEVANT ? 'Remove from "relevant"' : 'Mark as "relevant"';
};

const getNotRelevantTooltipText = (law: PreprocessedLaw) => {
  return law.category === Category.NOT_RELEVANT
    ? 'Remove from "not relevant"'
    : 'Mark as "not relevant"';
};

const getRelevancyBadgeText = (law: PreprocessedLaw): string => {
  return isLikelyRelevant(law) ? 'Likely Relevant' : 'Likely Not Relevant';
};

const getRelevancyBadgeVariant = (law: PreprocessedLaw): 'warning' | 'neutral' => {
  return isLikelyRelevant(law) ? 'warning' : 'neutral';
};

const getRelevancyTooltipText = (law: PreprocessedLaw): string => {
  return isLikelyRelevant(law)
    ? 'Our AI system classified this law as relevant for at least one of the teams of your organization. Expand this for more details.'
    : 'Our AI system classified this law as not relevant for each team of your organization. Note that our AI system can make mistakes and human review is necessary.';
};

const getLawEffectDateText = (law: PreprocessedLaw): string => {
  return law.effect_date ? ` on ${formatGermanDate(law.effect_date)}` : '';
};

const getLawEffectEndDateText = (law: PreprocessedLaw): string => {
  return law.end_validity_date && new Date(law.end_validity_date).getFullYear() !== 9999
    ? ` until ${formatGermanDate(law.end_validity_date)}`
    : '';
};
</script>

<template>
  <AaAccordion v-slot="accordionProps">
    <AaAccordionSection
      v-for="law in laws"
      :key="getSectionId(law.law_file_id)"
      :id="getSectionId(law.law_file_id)"
      :current="accordionProps.current"
      v-slot="sectionProps"
    >
      <AaAccordionTrigger
        :active="sectionProps.active"
        @click="accordionProps.onToggleItem(getSectionId(law.law_file_id))"
        class="bg-core-bg-primary my-1"
      >
        <div class="w-full min-w-20">
          <AaText class="whitespace-normal break-words pr-2" size="sm">
            {{ law.title }}
          </AaText>
          <div class="mb-1 mt-2 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <AaInfoBadge
                v-if="law.status !== 'PROCESSED'"
                :soft="true"
                :variant="getBadgeVariant(law.status)"
                prepend-icon="i-material-symbols-smart-toy-outline"
                class="min-w-35 justify-center"
              >
                {{ getStatusDisplayText(law.status) }}
              </AaInfoBadge>
              <AaInfoBadge
                v-if="law.team_relevancy_classification?.length"
                :ref="(el) => (relevancyBadgeRefs[law.law_file_id] = el as HTMLElement)"
                :soft="true"
                :variant="getRelevancyBadgeVariant(law)"
                prepend-icon="i-material-symbols-smart-toy-outline"
                class="min-w-35 justify-center"
              >
                {{ getRelevancyBadgeText(law) }}
              </AaInfoBadge>
              <AaTooltip
                v-if="
                  relevancyBadgeRefs[law.law_file_id] && law.team_relevancy_classification?.length
                "
                :anchor="relevancyBadgeRefs[law.law_file_id]"
                placement="top"
                :z-index="10"
              >
                {{ getRelevancyTooltipText(law) }}
              </AaTooltip>
              <span class="text-core-content-tertiary">|</span>
              <AaText
                size="xs"
                :class="[
                  'font-bold',
                  getRelevantTeams(law).length >= 1
                    ? 'text-semantic-content-error-soft'
                    : 'text-core-content-tertiary',
                ]"
              >
                Affects {{ getRelevantTeams(law).length }} Team(s){{ getLawEffectDateText(law)
                }}{{ getLawEffectEndDateText(law) }}
              </AaText>
            </div>

            <div class="flex gap-4">
              <AaButton
                :ref="(el) => (relevantButtonRefs[law.law_file_id] = el as HTMLElement)"
                prepend-icon="i-material-symbols-cognition2-outline"
                variant="outline"
                :disabled="lawCoordinatorStore.isCategoryLoading(law.law_file_id)"
                @click.stop="handleCategoryChange(law.law_file_id, Category.RELEVANT)"
                :class="[
                  'relevancy-button',
                  'rounded-2xl',
                  law.category === Category.RELEVANT && 'button-relevant',
                ]"
              >
                Relevant
              </AaButton>

              <AaButton
                :ref="(el) => (notRelevantButtonRefs[law.law_file_id] = el as HTMLElement)"
                prepend-icon="i-material-symbols-cognition2-outline"
                variant="outline"
                :disabled="lawCoordinatorStore.isCategoryLoading(law.law_file_id)"
                @click.stop="handleCategoryChange(law.law_file_id, Category.NOT_RELEVANT)"
                :class="[
                  'relevancy-button',
                  'rounded-2xl',
                  law.category === Category.NOT_RELEVANT && 'button-not-relevant',
                ]"
              >
                Not Relevant
              </AaButton>
              <AaTooltip
                v-if="relevantButtonRefs[law.law_file_id]"
                :anchor="relevantButtonRefs[law.law_file_id]"
                placement="top"
                :z-index="10"
              >
                {{ getRelevantTooltipText(law) }}
              </AaTooltip>

              <AaTooltip
                v-if="notRelevantButtonRefs[law.law_file_id]"
                :anchor="notRelevantButtonRefs[law.law_file_id]"
                placement="top"
                :z-index="10"
              >
                {{ getNotRelevantTooltipText(law) }}
              </AaTooltip>
            </div>
          </div>
        </div>
      </AaAccordionTrigger>
      <AaAccordionContent :active="sectionProps.active" class="bg-white">
        <MonitoringDisplayAccordionContent
          :law="law"
          @open-full-report="emit('open-full-report', $event)"
          @download-pdf-report="emit('download-pdf-report', $event)"
          @download-word-report="emit('download-word-report', $event)"
        />
      </AaAccordionContent>
    </AaAccordionSection>
  </AaAccordion>
</template>

<style scoped>
.relevancy-button:hover {
  background-color: #f0f0f0;
}

.button-relevant {
  border-radius: 30px;
  background-color: #dcfce7;
  border-color: #15803d;
  color: #15803d;
}

.button-relevant:hover {
  background-color: #dcfce7;
  border-color: #0a3d1d;
  color: #0a3d1d;
}

.button-not-relevant {
  background-color: #fee2e2;
  border-color: #991b1b;
  color: #991b1b;
}

.button-not-relevant:hover {
  background-color: #fee2e2;
  border-color: #360a0a;
  color: #360a0a;
}
</style>

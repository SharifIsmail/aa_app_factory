<script setup lang="ts">
import { Timeline, TimelineItem } from '../../common/components';
import type { ExplainedStep } from '@/types';
import { AaText, AaButton } from '@aleph-alpha/ds-components-vue';
import { computed, ref } from 'vue';

const props = defineProps<{
  explainedSteps?: ExplainedStep[] | null;
}>();

const isExpanded = ref(true); // Expanded by default

const explainedSteps = computed(() => {
  return props.explainedSteps || [];
});

const isLastStep = (index: number) => {
  if (explainedSteps.value.length === 0) return false;
  return index === explainedSteps.value.length - 1;
};

const toggleExpansion = () => {
  isExpanded.value = !isExpanded.value;
};
</script>

<template>
  <div v-if="explainedSteps.length > 0" class="mb-8">
    <AaButton
      class="text-core-content-secondary hover:text-core-content-primary mb-2"
      variant="text"
      size="small"
      @click="toggleExpansion()"
      :append-icon="
        isExpanded
          ? 'i-material-symbols-keyboard-arrow-up'
          : 'i-material-symbols-keyboard-arrow-down'
      "
    >
      Schritte
    </AaButton>

    <div v-if="isExpanded">
      <Timeline>
        <TimelineItem
          v-for="(step, index) in explainedSteps"
          :key="step.time_start"
          :is-last="isLastStep(index)"
        >
          <AaText
            v-if="step.explanation"
            size="xs"
            wrap="prewrap"
            class="mb-3 italic"
            color="text-core-content-placeholder"
          >
            {{ step.explanation }}
          </AaText>
        </TimelineItem>
      </Timeline>
    </div>
  </div>
</template>

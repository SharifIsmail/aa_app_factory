<script setup lang="ts">
import { CodeBlock, Timeline, TimelineItem } from '@/common/components';
import type { ExplainedStep } from '@/types';
import { AaCircularLoading, AaText, AaButton } from '@aleph-alpha/ds-components-vue';
import { ref, watch, computed } from 'vue';

const props = defineProps<{
  explainedSteps?: ExplainedStep[] | null;
  isSearching?: boolean;
}>();

const expandedSteps = ref<Record<number, boolean>>({});

watch(
  () => props.explainedSteps,
  () => {
    expandedSteps.value = {};
  }
);

const toggleStep = (stepIndex: number) => {
  expandedSteps.value[stepIndex] = !expandedSteps.value[stepIndex];
};

const isStepExpanded = (stepIndex: number) => {
  return expandedSteps.value[stepIndex] || false;
};

const hasCodeBlocks = (step: any) => {
  return step.executed_code || step.execution_log || step.code_output;
};

const stepNumbers = computed(() => {
  if (!props.explainedSteps) return [];

  let mainStep = 0;
  let subStep = 0;
  let previousWasDataAnalysis = false;

  return props.explainedSteps.map((step) => {
    const isDataAnalysis = step.agent_name === 'data_analysis_agent';

    if (isDataAnalysis) {
      if (previousWasDataAnalysis) {
        subStep++;
      } else {
        subStep = 1;
      }
      previousWasDataAnalysis = true;
      return { main: mainStep, sub: subStep, isDataAnalysis: true };
    } else {
      if (previousWasDataAnalysis) {
        mainStep++;
      } else {
        mainStep++;
      }
      subStep = 0;
      previousWasDataAnalysis = false;
      return { main: mainStep, sub: 0, isDataAnalysis: false };
    }
  });
});

const getStepLabel = (index: number) => {
  const stepNum = stepNumbers.value[index];
  if (!stepNum) return `Schritt ${index + 1}`;

  if (stepNum.isDataAnalysis) {
    return `Schritt ${stepNum.main}.${stepNum.sub} (Tiefe Datenanalyse)`;
  } else {
    return `Schritt ${stepNum.main}`;
  }
};

const isDataAnalysisStep = (index: number) => {
  return stepNumbers.value[index]?.isDataAnalysis || false;
};
</script>

<template>
  <Timeline>
    <!-- Loading State -->
    <TimelineItem v-if="isSearching">
      <div class="text-core-content-secondary align-flex-start flex gap-2 text-sm text-xs italic">
        Detaillierte Schritte werden in Kürze verfügbar sein... <AaCircularLoading />
      </div>
    </TimelineItem>

    <!-- Timeline when not searching -->
    <template v-if="!isSearching">
      <!-- Started -->
      <TimelineItem>
        <AaText size="sm" weight="semibold" class="italic" color="text-core-content-placeholder">
          Gestartet
        </AaText>
      </TimelineItem>

      <!-- Steps -->
      <TimelineItem v-for="(step, index) in explainedSteps" :key="step.time_start">
        <div :class="{ 'ml-8': isDataAnalysisStep(index) }">
          <AaText
            size="sm"
            weight="semibold"
            class="mb-2 italic"
            color="text-core-content-placeholder"
          >
            {{ getStepLabel(index) }}
          </AaText>
          <AaText
            v-if="step.explanation"
            size="sm"
            wrap="prewrap"
            class="mb-3"
            color="text-core-content-placeholder"
          >
            {{ step.explanation }}
          </AaText>
          <div v-if="hasCodeBlocks(step)">
            <AaButton
              variant="text"
              size="small"
              @click="toggleStep(index)"
              :append-icon="
                isStepExpanded(index)
                  ? 'i-material-symbols-keyboard-arrow-up'
                  : 'i-material-symbols-keyboard-arrow-down'
              "
            >
              <AaText size="xs" color="text-core-content-placeholder">Details</AaText>
            </AaButton>
          </div>
          <div v-if="isStepExpanded(index)" class="space-y-3">
            <CodeBlock
              v-if="step.executed_code"
              class="max-w-3xl"
              :content="step.executed_code"
              title="Python Code"
            />
            <CodeBlock
              v-if="step.execution_log"
              class="max-w-3xl"
              :content="step.execution_log"
              title="Execution Log"
            />
            <CodeBlock
              v-if="step.code_output"
              class="max-w-3xl"
              :content="step.code_output"
              title="Output"
            />
          </div>
        </div>
      </TimelineItem>

      <!-- Finished -->
      <TimelineItem :is-last="true">
        <AaText size="sm" weight="semibold" class="italic" color="text-core-content-placeholder">
          Fertig
        </AaText>
      </TimelineItem>
    </template>
  </Timeline>
</template>

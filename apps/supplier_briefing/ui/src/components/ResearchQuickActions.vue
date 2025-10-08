<script setup lang="ts">
import {
  QuickActionCompareBranchRisks,
  QuickActionRisks,
  QuickActionSummarize,
} from './QuickActions';
import { AaButton } from '@aleph-alpha/ds-components-vue';
import { ref, watch, computed } from 'vue';

type Action = 'summarize' | 'risks' | 'compare_branch_risks';

const QUICK_ACTIONS_CONFIG: Record<
  Action,
  { flowName: string; requiresPartner: boolean; queryText: string }
> = {
  summarize: {
    flowName: 'summarize_business_partner',
    requiresPartner: true,
    queryText: 'Summarize the selected business partner.',
  },
  risks: {
    flowName: 'business_partner_risks',
    requiresPartner: true,
    queryText: 'Analyze risks for the selected business partner.',
  },
  compare_branch_risks: {
    flowName: 'compare_branch_risks',
    requiresPartner: false,
    queryText: 'Compare risks across different branches.',
  },
};

const props = defineProps<{
  isDisabled: boolean;
  isSearching: boolean;
}>();

const emit = defineEmits<{
  (e: 'process', payload: { flowName: string; params: object; queryText: string }): void;
  (e: 'action-state-changed', hasActiveAction: boolean): void;
}>();

const activeAction = ref<Action | null>(null);
const selectedPartnerId = ref<string | null>(null);

const isProcessButtonDisabled = computed(() => {
  if (!activeAction.value) return true;
  const config = QUICK_ACTIONS_CONFIG[activeAction.value];
  return config.requiresPartner && !selectedPartnerId.value;
});

const selectAction = (action: Action) => {
  if (props.isDisabled || props.isSearching) return;
  activeAction.value = action;
};

const onPartnerSelected = (partnerId: string | null) => {
  selectedPartnerId.value = partnerId;
};

const onProcess = () => {
  if (!activeAction.value) return;

  const config = QUICK_ACTIONS_CONFIG[activeAction.value];
  const params = config.requiresPartner ? { business_partner_id: selectedPartnerId.value } : {};

  emit('process', { flowName: config.flowName, params, queryText: config.queryText });
};

const onCancel = () => {
  activeAction.value = null;
  selectedPartnerId.value = null;
};

watch(activeAction, (newValue) => {
  emit('action-state-changed', newValue !== null);
});
</script>

<template>
  <div class="mb-3 flex flex-wrap gap-2">
    <template v-if="!activeAction">
      <QuickActionSummarize
        :is-disabled="props.isDisabled"
        :is-searching="props.isSearching"
        @click="() => selectAction('summarize')"
      />
      <QuickActionRisks
        :is-disabled="props.isDisabled"
        :is-searching="props.isSearching"
        @click="() => selectAction('risks')"
      />
      <QuickActionCompareBranchRisks
        :is-disabled="props.isDisabled"
        :is-searching="props.isSearching"
        @click="() => selectAction('compare_branch_risks')"
      />
    </template>
    <template v-else>
      <QuickActionSummarize
        v-if="activeAction === 'summarize'"
        :is-disabled="props.isDisabled"
        :is-searching="props.isSearching"
        :auto-open="true"
        @click="() => {}"
        @partner-selected="onPartnerSelected"
      />
      <QuickActionRisks
        v-if="activeAction === 'risks'"
        :is-disabled="props.isDisabled"
        :is-searching="props.isSearching"
        @click="() => {}"
      />
      <QuickActionCompareBranchRisks
        v-if="activeAction === 'compare_branch_risks'"
        :is-disabled="props.isDisabled"
        :is-searching="props.isSearching"
        @click="() => {}"
      />
    </template>
  </div>

  <div v-if="activeAction" class="flex items-center justify-end gap-2">
    <AaButton variant="text" @click="onCancel">Cancel</AaButton>
    <AaButton :disabled="isProcessButtonDisabled" variant="primary" @click="onProcess"
      >Process</AaButton
    >
  </div>
</template>

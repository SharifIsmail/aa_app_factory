<script setup lang="ts">
import ColumnSuggestionsDropdown from './ColumnSuggestionsDropdown.vue';
import ResearchQuickActions from './ResearchQuickActions.vue';
import { useColumnsStore } from '@/stores/useColumnsStore';
import { useDataPreparationStore } from '@/stores/useDataPreparationStore';
import { computeDropdownPosition } from '@/utils/caretPosition.ts';
import { bestColumnMatches } from '@/utils/columnMatching';
import { computeSuggestionInsertion } from '@/utils/suggestionInsertion';
import { AaIconButton } from '@aleph-alpha/ds-components-vue';
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue';

// Feature flag - set to true to enable Quick Actions
const ENABLE_QUICK_ACTIONS = false;

const userQuestion = ref('');
const dataPreparationStore = useDataPreparationStore();
const columnsStore = useColumnsStore();
const isQuickActionActive = ref(false);

const emit = defineEmits<{
  (e: 'start-search', question: string, flowName?: string, params?: object): void;
  (e: 'stop-search'): void;
}>();

const props = defineProps<{
  hasMessages: boolean;
  isSearching: boolean;
}>();

const isDisabled = computed(() => {
  return !dataPreparationStore.isReady || props.isSearching;
});

const textAreaRef = ref<HTMLTextAreaElement>();
const containerRef = ref<HTMLElement>();
const caretIndex = ref<number>(0);
const dropdownManuallyClosed = ref<boolean>(false);

const suggestions = computed(() => {
  const caret = caretIndex.value;
  const prefix = userQuestion.value.slice(0, caret);
  return bestColumnMatches(columnsStore.columns, prefix, 5);
});

const isDropdownOpen = computed(
  () => suggestions.value.length > 0 && !dropdownManuallyClosed.value
);
const highlightedIndex = ref<number>(-1);

type DropdownPosition = { left: number; top: number };
const dropdownPosition = ref<DropdownPosition>({ left: 0, top: 0 });

const updateDropdownPosition = async () => {
  await nextTick();
  const textarea = textAreaRef.value;
  const container = containerRef.value;
  if (!textarea || !container) return;

  const caret = caretIndex.value;
  const { left, top } = computeDropdownPosition({
    textarea,
    container,
    caretIndex: caret,
    dropdownWidth: 240,
    verticalOffset: 30,
  });

  dropdownPosition.value = { left, top };
};

const closeDropdown = () => {
  highlightedIndex.value = -1;
  dropdownManuallyClosed.value = true;
};

const selectSuggestion = async (suggestion: string) => {
  const el = textAreaRef.value;
  const current = userQuestion.value;
  const caret = el ? (el.selectionStart ?? current.length) : current.length;

  const { newText, newCaretIndex } = computeSuggestionInsertion(current, suggestion, caret);

  userQuestion.value = newText;
  await nextTick();
  if (el) {
    el.setSelectionRange(newCaretIndex, newCaretIndex);
  }
  closeDropdown();
};

const updateCaretIndex = () => {
  const el = textAreaRef.value;
  caretIndex.value = el
    ? (el.selectionStart ?? userQuestion.value.length)
    : userQuestion.value.length;
  void updateDropdownPosition();
};

const submitQuestion = () => {
  if (isDisabled.value) return;

  const question = userQuestion.value.trim();
  if (question) {
    userQuestion.value = '';
    emit('start-search', question);
  }
};

const handleQuickActionStateChange = (hasActiveAction: boolean) => {
  isQuickActionActive.value = hasActiveAction;
};

const handleQuickActionProcess = (payload: {
  flowName: string;
  params: object;
  queryText: string;
}) => {
  if (isDisabled.value) return;
  // Emit start-search with structured flow data AND the natural language query
  emit('start-search', payload.queryText, payload.flowName, payload.params);
};

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowDown') {
    if (suggestions.value.length > 0 && isDropdownOpen.value) {
      highlightedIndex.value =
        (highlightedIndex.value + 1 + suggestions.value.length) % suggestions.value.length;
      event.preventDefault();
    }
    return;
  }
  if (event.key === 'ArrowUp') {
    if (suggestions.value.length > 0 && isDropdownOpen.value) {
      highlightedIndex.value =
        (highlightedIndex.value - 1 + suggestions.value.length) % suggestions.value.length;
      event.preventDefault();
    }
    return;
  }
  if (event.key === 'Enter' && !event.shiftKey) {
    if (isDropdownOpen.value && highlightedIndex.value >= 0) {
      const suggestion = suggestions.value[highlightedIndex.value];
      event.preventDefault();
      void selectSuggestion(suggestion);
      return;
    }
    event.preventDefault();
    submitQuestion();
    return;
  }
  if (event.key === 'Tab') {
    if (suggestions.value.length > 0 && isDropdownOpen.value) {
      event.preventDefault();
      const suggestion = suggestions.value[0];
      void selectSuggestion(suggestion);
    }
    return;
  }
  if (event.key === 'Escape') {
    closeDropdown();
    return;
  }
};

const autoResize = (event: Event) => {
  const target = event.target as HTMLTextAreaElement;
  target.style.height = 'auto';
  target.style.height = `${target.scrollHeight}px`;
};

const onInput = (event: Event) => {
  dropdownManuallyClosed.value = false;
  autoResize(event);
  updateCaretIndex();
};

const onScroll = () => {
  void updateDropdownPosition();
};

onMounted(() => {
  window.addEventListener('resize', updateDropdownPosition);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateDropdownPosition);
});

watch([userQuestion, caretIndex, () => isDropdownOpen.value], () => {
  if (isDropdownOpen.value) void updateDropdownPosition();
});
</script>

<template>
  <div :class="{ 'mx-auto w-2/3 max-w-4xl': true, 'mt-48': !props.hasMessages }">
    <!-- Title -->
    <div v-if="!props.hasMessages" class="mb-6 text-center">
      <h1 class="text-core-content-primary text-2xl font-medium">
        What would you like to know about the Supplier data?
      </h1>
    </div>

    <ResearchQuickActions
      v-if="ENABLE_QUICK_ACTIONS"
      :is-disabled="isDisabled"
      :is-searching="props.isSearching"
      @action-state-changed="handleQuickActionStateChange"
      @process="handleQuickActionProcess"
    />

    <div
      v-if="!isQuickActionActive"
      class="bg-core-bg-tertiary border-core-border-contrast hover:border-core-border-contrast-hover [&:has(textarea:focus)]:border-core-border-focus relative flex flex-col rounded border p-3 [&:has(textarea:focus)]:border-2"
      ref="containerRef"
    >
      <div class="flex items-baseline gap-3">
        <!-- Input Field -->
        <div class="flex-1">
          <textarea
            v-model="userQuestion"
            placeholder="Ask me something..."
            class="scrollbar-thin text-core-content-secondary bg-core-bg-primary placeholder-core-content-placeholder max-h-[60px] min-h-[60px] w-full resize-none overflow-y-auto border-none focus:outline-none"
            rows="3"
            :disabled="isDisabled"
            ref="textAreaRef"
            @keydown="handleKeyDown"
            @input="onInput"
            @click="updateCaretIndex"
            @keyup="updateCaretIndex"
            @scroll="onScroll"
          />
        </div>
        <AaIconButton
          v-if="!isSearching"
          @click="submitQuestion"
          :disabled="!userQuestion.trim() || isDisabled"
          icon="i-material-symbols-send"
          variant="primary"
          label="Send Query"
        />
        <AaIconButton
          v-if="isSearching"
          @click="emit('stop-search')"
          icon="i-material-symbols-square-rounded"
          variant="primary"
          label="Cancel Query"
        />
      </div>

      <!-- Suggestions Dropdown -->
      <ColumnSuggestionsDropdown
        :suggestions="suggestions"
        :is-open="isDropdownOpen"
        :highlighted-index="highlightedIndex"
        :position="dropdownPosition"
        @select-suggestion="selectSuggestion"
        @close-dropdown="closeDropdown"
        @highlight-index-change="highlightedIndex = $event"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { AaButton, AaInput, AaText } from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

interface Props {
  lawUrl: string;
  urlError?: string;
  isComputingSummary?: boolean;
}

interface Emits {
  (e: 'update:lawUrl', value: string): void;
  (e: 'generate-report'): void;
}

const props = withDefaults(defineProps<Props>(), {
  urlError: '',
  isComputingSummary: false,
});

const emit = defineEmits<Emits>();

// URL validation
const isValidUrl = computed(() => {
  if (!props.lawUrl) return true;
  return props.lawUrl.includes('eur-lex.europa.eu');
});

const buttonDisabled = computed(() => {
  return !props.lawUrl.trim() || !isValidUrl.value || props.isComputingSummary;
});

const handleInputChange = (value: string | number | undefined) => {
  emit('update:lawUrl', String(value || ''));
};

const handleGenerate = () => {
  if (buttonDisabled.value) return;
  emit('generate-report');
};
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Input field -->
    <div class="flex flex-col">
      <AaInput
        :model-value="lawUrl"
        placeholder="Paste EUR-Lex URL here"
        size="medium"
        :state="urlError ? 'error' : 'default'"
        prepend-icon="i-material-symbols-search"
        @update:model-value="handleInputChange"
        @keydown.enter="handleGenerate"
      />
    </div>

    <!-- Generate button and EU Legislation DB button on same level -->
    <div class="flex justify-between gap-3">
      <AaButton
        variant="text"
        size="small"
        href="https://eur-lex.europa.eu/search.html?name=collection%3Aeu-law-legislation&type=named&qid=1745521085009"
      >
        EU Legislation Database
      </AaButton>

      <AaButton
        prepend-icon="i-material-symbols-summarize-outline"
        :disabled="buttonDisabled"
        :loading="isComputingSummary"
        @click="handleGenerate"
      >
        {{ isComputingSummary ? 'Validating URL...' : 'Generate Legal Act Report' }}
      </AaButton>
    </div>

    <!-- Error message display -->
    <div v-if="urlError">
      <AaText element="p" size="sm" class="text-semantic-content-error" role="alert">{{
        urlError
      }}</AaText>
    </div>
  </div>
</template>

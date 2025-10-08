<script setup lang="ts">
import { AaButton } from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

const props = defineProps<{
  isDisabled: boolean;
  isSearching: boolean;
}>();

const emit = defineEmits<{
  (e: 'click'): void;
}>();

const disabled = computed(() => props.isDisabled || props.isSearching);
</script>

<template>
  <AaButton :disabled="disabled" variant="secondary" @click="emit('click')">
    Compare Branch Risks
  </AaButton>
</template>

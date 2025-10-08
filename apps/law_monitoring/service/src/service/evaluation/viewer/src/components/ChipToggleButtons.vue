<script setup lang="ts">
import { AaText } from '@aleph-alpha/ds-components-vue';
import { computed, type ComputedRef } from 'vue';

const CHIP_STYLES = {
  COMMON:
    'flex flex-row items-center gap-3XS rounded-full p-y-XS p-x-M heading-14 border border-core-border-default outline-none',
  UNSELECTED:
    'focus:ring-2 ring-core-border-focus enabled:hover:bg-core-bg-tertiary-hover text-core-content-secondary enabled:hover:text-core-content-primary',
  SELECTED:
    'bg-core-bg-accent-soft text-core-content-accent-soft ring-core-border-focus enabled:hover:bg-core-bg-accent-soft-hover enabled:focus:ring-2',
  DISABLED: 'opacity-50',
} as const;

interface ChipOption {
  readonly value: string;
  readonly label: string;
  readonly prependIcon?: string;
}

interface Props {
  title: string;
  modelValue: string;
  options: readonly ChipOption[];
  mandatory?: boolean;
  disabled?: boolean;
}

interface Emits {
  (event: 'update:modelValue', value: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  mandatory: false,
  disabled: false,
});

const emit = defineEmits<Emits>();

const isOptionSelected: ComputedRef<(optionValue: string) => boolean> = computed(() => {
  return (optionValue: string): boolean => props.modelValue === optionValue;
});

const handleChipSelection = (optionValue: string): void => {
  if (props.disabled) return;

  if (props.mandatory && props.modelValue === optionValue) {
    return;
  }

  emit('update:modelValue', optionValue);
};

const getChipClasses = (optionValue: string): Record<string, boolean> => {
  const isSelected = isOptionSelected.value(optionValue);

  return {
    [CHIP_STYLES.COMMON]: true,
    [CHIP_STYLES.UNSELECTED]: !props.disabled && !isSelected,
    [CHIP_STYLES.SELECTED]: !props.disabled && isSelected,
    [CHIP_STYLES.DISABLED]: props.disabled,
  };
};

const getTextClasses = (optionValue: string): string => {
  const isSelected = isOptionSelected.value(optionValue);
  return isSelected ? 'chip-text-selected' : '';
};
</script>

<template>
  <div class="flex items-center gap-2" role="group" :aria-label="`${title} selection`">
    <AaText size="sm" weight="bold" class="text-core-content-tertiary">
      {{ title }}
    </AaText>

    <button
      v-for="option in options"
      :key="option.value"
      :class="getChipClasses(option.value)"
      :disabled="disabled"
      @click="handleChipSelection(option.value)"
    >
      <span v-if="option.prependIcon" :class="option.prependIcon" />
      <AaText size="sm" :class="getTextClasses(option.value)">
        {{ option.label }}
      </AaText>
    </button>
  </div>
</template>

<style scoped>
.chip-text-selected {
  color: #3c26eb;
}
</style>

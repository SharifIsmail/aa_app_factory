<script setup lang="ts">
import Popover from './Popover.vue';
import type { ExportFormat } from '@/@core/composables/useWidgetExport';
import { AaButton, type AaButtonProps } from '@aleph-alpha/ds-components-vue';

interface Props {
  /** Export format options */
  exportOptions: ExportFormat[];
  /** Whether the export is disabled */
  disabled?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Button variant */
  variant?: AaButtonProps['variant'];
  /** Button size */
  size?: AaButtonProps['size'];
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  loading: false,
  variant: 'text',
  size: 'medium',
});

const emit = defineEmits<{
  export: [format: string];
}>();

const handleExport = (format: string) => {
  emit('export', format);
};
</script>

<template>
  <Popover placement="bottom-end" width="200px" style="min-height: fit-content">
    <template #trigger="{ toggle }">
      <AaButton
        :variant="props.variant"
        :size="props.size"
        prepend-icon="i-material-symbols-download"
        append-icon="i-material-symbols-keyboard-arrow-down"
        label="Export Widget"
        aria-label="Export Widget"
        :disabled="props.disabled || props.loading"
        :loading="props.loading"
        @click="toggle"
      />
    </template>

    <div class="py-2">
      <AaButton
        v-for="option in props.exportOptions"
        :key="option.value"
        :disabled="props.disabled || props.loading"
        :prepend-icon="option?.icon"
        @click="handleExport(option.value)"
        variant="text"
      >
        {{ option.label }}
      </AaButton>
    </div>
  </Popover>
</template>

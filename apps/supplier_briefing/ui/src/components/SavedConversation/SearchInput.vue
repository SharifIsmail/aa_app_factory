<script lang="ts" setup>
import { AaInput, AaIconButton } from '@aleph-alpha/ds-components-vue';

interface Props {
  modelValue: string;
  placeholder?: string;
}

interface Emits {
  (e: 'update:modelValue', value: string): void;
}

withDefaults(defineProps<Props>(), {
  placeholder: 'Search...',
});

const emit = defineEmits<Emits>();

function updateValue(value?: string | number): void {
  emit('update:modelValue', String(value ?? ''));
}
</script>

<template>
  <div class="relative">
    <AaInput
      :model-value="modelValue"
      size="small"
      :placeholder="placeholder"
      class="w-full"
      prepend="i-material-symbols-search"
      @update:model-value="updateValue"
    >
      <template #prepend>
        <span class="i-material-symbols-search m-auto ml-2"></span>
      </template>
      <template v-if="modelValue.trim().length > 0" #append>
        <AaIconButton
          variant="ghost"
          icon="i-material-symbols-close"
          label="Clear search"
          @click="updateValue('')"
        />
      </template>
    </AaInput>
  </div>
</template>

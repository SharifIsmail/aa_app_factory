<script setup lang="ts">
import MultiSelect from './MultiSelect.vue';
import { useEurovocStore } from '@/modules/monitoring/stores/eurovocStore.ts';
import { onMounted } from 'vue';

interface Props {
  modelValue: string[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  ariaDescribedBy?: string;
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Select Eurovoc descriptors...',
  disabled: false,
  required: false,
  ariaDescribedBy: '',
});

const emit = defineEmits<Emits>();
const eurovocStore = useEurovocStore();

onMounted(() => {
  eurovocStore.fetchEurovocDescriptors();
});
</script>

<template>
  <MultiSelect
    :model-value="props.modelValue"
    :options="eurovocStore.eurovocDescriptors"
    :loading="eurovocStore.isLoadingDescriptors"
    :placeholder="props.placeholder"
    search-placeholder="Search Eurovoc descriptors..."
    :disabled="props.disabled"
    :required="props.required"
    :aria-described-by="props.ariaDescribedBy"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>

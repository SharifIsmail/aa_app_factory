<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  /** Additional CSS classes to apply to the button */
  class?: string;
  /** Button variant for different styling */
  variant?: 'default' | 'compact' | 'outline';
  /** Icon to prepend to the button */
  prependIcon?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  class: '',
  prependIcon: '',
});

const emit = defineEmits<{
  click: [];
}>();

const buttonClasses = computed(() => {
  const baseClasses =
    'px-1 py-0.5 inline-flex items-center gap-1 rounded-md text-xs hover:cursor-pointer transition-all duration-200';

  const variantClasses = {
    default:
      'bg-core-bg-secondary hover:bg-core-bg-accent text-core-content-primary hover:text-core-bg-primary border-core-border-hover',
    compact:
      'bg-blue-100 hover:bg-blue-200 text-blue-800 hover:text-blue-800 border border-blue-200 hover:border-blue-300',
    outline:
      'border border-gray-300 hover:border-gray-400 text-gray-600 hover:text-gray-800 hover:bg-gray-50',
  };

  return `${baseClasses} ${variantClasses[props.variant]} ${props.class}`;
});

const handleClick = () => {
  emit('click');
};
</script>

<template>
  <button :class="buttonClasses" @click="handleClick" type="button">
    <i v-if="prependIcon" :class="prependIcon" class="shrink-0" aria-hidden="true" />
    <slot />
  </button>
</template>

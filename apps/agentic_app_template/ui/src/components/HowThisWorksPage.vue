<script setup lang="ts">
import { AaButton } from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

const props = defineProps<{
  prev?: { value: string; label: string };
  next?: { value: string; label: string };
  wrapperClass?: string;
}>();
const emit = defineEmits<{ (e: 'navigate', value: string): void }>();
const justifyClass = computed(() =>
  props.prev && props.next ? 'justify-between' : props.prev ? 'justify-start' : 'justify-end'
);
</script>

<template>
  <div :class="wrapperClass">
    <slot />
    <div :class="['mt-6 flex', justifyClass]">
      <AaButton
        v-if="prev"
        @click="emit('navigate', prev.value)"
        variant="outline"
        size="medium"
        prepend-icon="i-material-symbols-arrow-back"
      >
        Back: {{ prev.label }}
      </AaButton>
      <AaButton
        v-if="next"
        @click="emit('navigate', next.value)"
        variant="secondary"
        size="medium"
        append-icon="i-material-symbols-arrow-forward"
      >
        Next: {{ next.label }}
      </AaButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Comment, ref } from 'vue';
import type { VNode } from 'vue';

const containerRef = ref<HTMLElement>();

defineExpose({
  containerRef,
});
</script>
<template>
  <section
    ref="containerRef"
    class="bg-core-bg-secondary flex h-full max-h-screen flex-1 flex-col items-start"
  >
    <header
      v-if="$slots.title && $slots.title({}).filter((n: VNode) => n.type !== Comment).length"
      class="w-full"
    >
      <slot name="title" />
    </header>
    <slot />
  </section>
</template>

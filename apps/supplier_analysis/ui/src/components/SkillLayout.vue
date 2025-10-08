<script setup lang="ts">
import { Comment } from 'vue';
import type { VNode } from 'vue';
</script>
<template>
  <section class="bg-core-bg-secondary flex h-screen flex-col items-start">
    <header
      v-if="$slots.title && $slots.title({}).filter((n: VNode) => n.type !== Comment).length"
      class="flex flex-shrink-0 flex-col self-stretch"
    >
      <div
        class="px-XL core-border-default flex h-14 flex-shrink-0 items-center justify-between border-b py-2.5"
      >
        <div class="flex flex-row gap-2">
          <slot name="title" />
        </div>
      </div>
    </header>
    <slot />
  </section>
</template>

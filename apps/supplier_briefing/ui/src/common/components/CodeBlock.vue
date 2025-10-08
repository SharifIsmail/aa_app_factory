<script setup lang="ts">
import { computed, ref } from 'vue';

interface Props {
  content: string;
  title?: string;
}

const MAX_CONTENT_LENGTH = 400;

const props = withDefaults(defineProps<Props>(), {
  title: 'Code',
});

const isExpanded = ref(false);

const formattedContent = computed(() => {
  if (!props.content) return '';
  return props.content.replace(/\\n/g, '\n');
});

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};
</script>

<template>
  <div class="my-4 overflow-hidden rounded-xl shadow-lg">
    <div
      class="border-core-content-primary flex items-center justify-between border-b bg-gray-800 px-4 py-3"
    >
      <span class="text-core-content-always-white text-sm">{{ title }}</span>
      <div class="flex gap-2">
        <button
          v-if="content.length > MAX_CONTENT_LENGTH"
          @click="toggleExpand"
          class="border-core-border-default hover:bg-core-content-placeholder cursor-pointer rounded-md border bg-gray-600 px-3 py-1.5 text-xs font-medium text-gray-300 transition-all duration-200 hover:text-gray-50"
        >
          {{ isExpanded ? 'Collapse' : 'Expand' }}
        </button>
      </div>
    </div>
    <div
      class="bg-core-content-primary transition-all duration-300"
      :class="{ collapsed: !isExpanded && content.length > MAX_CONTENT_LENGTH }"
    >
      <pre
        class="text-core-content-always-white m-0 overflow-x-auto p-5 font-mono text-xs leading-relaxed"
      ><code class="bg-transparent p-0 font-mono text-inherit">{{ formattedContent }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.collapsed {
  max-height: 150px;
  overflow: hidden;
  position: relative;
}

.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  pointer-events: none;
  background: linear-gradient(transparent, #1f2937);
}

/* Scrollbar styling */
pre::-webkit-scrollbar {
  height: 6px;
}

pre::-webkit-scrollbar-track {
  background: #1e293b;
}

pre::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

pre::-webkit-scrollbar-thumb:hover {
  background: #64748b;
  cursor: pointer;
}
</style>

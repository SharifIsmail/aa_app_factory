<script setup lang="ts">
import { ref, onMounted } from 'vue';
import VueMarkdownRender from 'vue-markdown-render';

interface Props {
  /** The markdown content to render */
  content: string;
  /** Custom markdown-it options */
  options?: Record<string, any>;
  /** Whether to scroll to the first highlight after rendering
   * Highlighted content must be wrapped in <mark> tags
   */
  focusFirstHighlight?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  content: '',
  options: () => ({
    html: true,
    breaks: true,
    linkify: true,
    typographer: true,
  }),
  focusFirstHighlight: false,
});

const markdownRenderer = ref<any>(null);

onMounted(() => {
  if (props.focusFirstHighlight && props.content && markdownRenderer.value) {
    const container = markdownRenderer.value?.$el;
    if (container) {
      const firstHighlight = container.querySelector('mark');
      if (firstHighlight) {
        firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
      }
    }
  }
});
</script>

<template>
  <div class="markdown-renderer-container">
    <div class="markdown-viewer">
      <VueMarkdownRender ref="markdownRenderer" :source="props.content" :options="props.options" />
    </div>
  </div>
</template>

<style scoped>
.markdown-renderer-container * {
  all: revert;
}

.markdown-renderer-container {
  width: 100%;
}

.markdown-viewer {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1.5rem;
  background-color: #fafafa;
  min-height: 200px;
}

/* Tables */
.markdown-renderer-container :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
  border: 1px solid #ddd;
}

.markdown-renderer-container :deep(th),
.markdown-renderer-container :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.markdown-renderer-container :deep(th) {
  background-color: #f5f5f5;
  font-weight: bold;
}

.markdown-renderer-container :deep(tr:nth-child(even)) {
  background-color: #f9f9f9;
}
</style>

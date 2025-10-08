<script lang="ts" setup>
import { AaText } from '@aleph-alpha/ds-components-vue';

interface Props {
  isSearching: boolean;
}

defineProps<Props>();
</script>

<template>
  <div class="flex flex-1 items-center justify-center p-8">
    <div class="text-center">
      <span
        class="i-material-symbols-sms-outline text-core-content-tertiary mx-auto mb-4 block text-6xl"
      ></span>
      <AaText class="text-core-content-secondary">
        {{
          isSearching
            ? 'No conversations match your search'
            : 'No saved conversations or folders yet'
        }}
      </AaText>
      <AaText size="sm" class="text-core-content-tertiary mt-1">
        {{
          isSearching
            ? 'Try a different search term or clear your search'
            : 'Start a conversation and save it, or create folders to organize your chats'
        }}
      </AaText>
    </div>
  </div>
</template>

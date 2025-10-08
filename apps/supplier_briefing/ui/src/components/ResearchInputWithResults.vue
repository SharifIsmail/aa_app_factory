<script setup lang="ts">
import ResearchInputData from './ResearchInputData.vue';
import ResearchResultDisplay from './ResearchResultDisplay';
import { useConversationStore } from '@/stores/useConversationStore.ts';
import { useResearchAgentStore } from '@/stores/useResearchAgentStore';
import type { ConversationMessage, SearchCompleteData } from '@/types';
import { computed, ref, nextTick, onBeforeUnmount } from 'vue';

defineProps<{
  height: number;
}>();

const conversationStore = useConversationStore();
const researchAgentStore = useResearchAgentStore();

const activeConversation = computed(() => conversationStore.activeConversation);
const isSearching = computed(() => !!activeConversation.value?.isSearching);
const conversationMessages = computed(() => activeConversation.value?.messages || []);
const hasConversationMessages = computed(() => conversationMessages.value.length > 0);

const latestMessageRef = ref<HTMLElement | null>(null);

const setLatestMessageRef = (el: any, index: number) => {
  if (index === conversationMessages.value.length - 1) {
    latestMessageRef.value = el?.$el || el;
  }
};

// Scroll to the latest message
const scrollToLatestMessage = () => {
  if (latestMessageRef.value) {
    latestMessageRef.value.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    });
  }
};

const handleSearchComplete = (completionData: SearchCompleteData) => {
  const { answer, pandasObjectsData, explained_steps, resultsData } = completionData;
  const conversation = conversationStore.activeConversation;
  if (!conversation) return;

  conversationStore.updateLatestMessageInConversation(conversation.id, {
    answer,
    pandasObjectsData: pandasObjectsData,
    explained_steps,
    resultsData,
    status: 'completed',
  });

  conversationStore.setConversationSearching(conversation.id, false);
};

const handleSearchFailed = () => {
  const conversation = conversationStore.activeConversation;

  if (!conversation) return;

  if (conversation.messages.length > 0) {
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (lastMessage.status === 'pending') {
      conversationStore.updateLatestMessageInConversation(conversation.id, {
        answer: undefined,
        status: 'failed',
      });
    }
  }
  conversationStore.setConversationSearching(conversation.id, false);
};

const handleStatusUpdate = () => {
  const conversation = conversationStore.activeConversation;

  if (!conversation) return;

  if (conversation.messages.length > 0) {
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (lastMessage.status === 'pending') {
      conversationStore.updateLatestMessageInConversation(conversation.id, {
        answer: researchAgentStore.currentTask?.description,
        explained_steps: researchAgentStore.researchStatus?.explained_steps,
      });
    }
  }
};

const handleStartSearch = async (question: string, flowName?: string, params?: object) => {
  const conversation = conversationStore.getOrCreateActiveConversation();
  const conversationId = conversation.id;

  const searchId = await researchAgentStore.startResearch(
    question,
    handleSearchComplete,
    handleSearchFailed,
    handleStatusUpdate,
    conversationId,
    flowName,
    params
  );

  if (!searchId) {
    const failedMessage: ConversationMessage = {
      question,
      timestamp: new Date(),
      status: 'failed',
      answer: undefined,
    };
    conversationStore.addMessageToConversation(conversation.id, failedMessage);
    conversationStore.setConversationSearching(conversation.id, false);
    nextTick(() => {
      scrollToLatestMessage();
    });
    return;
  }

  const newMessage: ConversationMessage = {
    question,
    timestamp: new Date(),
    status: 'pending',
  };

  conversationStore.addMessageToConversation(conversation.id, newMessage);
  conversationStore.setConversationSearching(conversation.id, true);

  nextTick(() => {
    scrollToLatestMessage();
  });
};

const handleStopSearch = async () => {
  const conversation = conversationStore.activeConversation;
  if (!conversation) return;

  const success = await researchAgentStore.stopResearch();
  if (!success) return;

  if (conversation.messages.length > 0) {
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (lastMessage.status === 'pending') {
      conversationStore.updateLatestMessageInConversation(conversation.id, {
        status: 'stopped',
        answer: undefined,
      });
    }
  }

  conversationStore.setConversationSearching(conversation.id, false);
};

onBeforeUnmount(() => {
  researchAgentStore.reset();
});
</script>

<template>
  <div class="research-container mx-auto w-full pb-6 pt-6" :style="{ height: `${height}px` }">
    <div v-if="hasConversationMessages || isSearching" class="h-85/100 overflow-y-auto">
      <ResearchResultDisplay
        v-for="(message, index) in conversationMessages"
        :key="index"
        :ref="(el) => setLatestMessageRef(el, index)"
        :question="message.question"
        :answer="message.answer"
        :timestamp="message.timestamp.toLocaleString()"
        :pandas-objects-data="message.pandasObjectsData"
        :explained-steps="message.explained_steps"
        :results-data="message.resultsData"
        :is-searching="message.status === 'pending'"
        :is-failed="message.status === 'failed'"
      />
    </div>

    <ResearchInputData
      @start-search="handleStartSearch"
      @stop-search="handleStopSearch"
      :has-messages="hasConversationMessages"
      :is-searching="isSearching"
    />
  </div>
</template>

<style scoped>
.research-container {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
</style>

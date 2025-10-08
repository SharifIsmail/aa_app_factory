import { createStoreId } from '@/stores/createStoreId.ts';
import { useResearchAgentStore } from '@/stores/useResearchAgentStore';
import type {
  Conversation,
  ConversationMessage,
  ConversationHistory,
  SavedConversation,
  ConversationFolder,
} from '@/types/index.ts';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useConversationStore = defineStore(
  createStoreId('conversation'),
  () => {
    const activeConversation = ref<Conversation>();
    const conversationHistory = ref<ConversationHistory>({
      folders: [],
      savedConversations: [],
    });

    const activeConversationId = computed(() => activeConversation.value?.id);

    const createConversation = (): string => {
      const newId = crypto.randomUUID();
      const newConversation: Conversation = {
        id: newId,
        title: 'New Conversation',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        isSearching: false,
      };

      activeConversation.value = newConversation;
      return newId;
    };

    const getOrCreateActiveConversation = (): Conversation => {
      if (!activeConversationId.value || !activeConversation.value) {
        createConversation();
      }
      return activeConversation.value!;
    };

    const addMessageToConversation = (
      conversationId: string,
      message: ConversationMessage
    ): void => {
      if (activeConversation.value && activeConversation.value.id === conversationId) {
        activeConversation.value.messages.push(message);
        activeConversation.value.updatedAt = new Date();

        // Auto-generate title from first question
        if (activeConversation.value.messages.length === 1) {
          activeConversation.value.title = message.question;
        }

        // Auto-update saved version if this conversation was previously saved
        autoSaveConversationIfPreviouslySaved();
      }
    };

    const updateMessageInConversation = (
      conversationId: string,
      messageIndex: number,
      updates: Partial<ConversationMessage>
    ): void => {
      if (
        activeConversation.value &&
        activeConversation.value.id === conversationId &&
        activeConversation.value.messages[messageIndex]
      ) {
        Object.assign(activeConversation.value.messages[messageIndex], updates);
        activeConversation.value.updatedAt = new Date();

        // Auto-update saved version if this conversation was previously saved
        autoSaveConversationIfPreviouslySaved();
      }
    };

    const updateLatestMessageInConversation = (
      conversationId: string,
      updates: Partial<ConversationMessage>
    ): void => {
      if (
        activeConversation.value &&
        activeConversation.value.id === conversationId &&
        activeConversation.value.messages.length > 0
      ) {
        const lastIndex = activeConversation.value.messages.length - 1;
        updateMessageInConversation(conversationId, lastIndex, updates);
      }
    };

    const setConversationSearching = (conversationId: string, isSearching: boolean): void => {
      if (activeConversation.value && activeConversation.value.id === conversationId) {
        activeConversation.value.isSearching = isSearching;
        activeConversation.value.updatedAt = new Date();
      }
    };

    const startNewConversation = async (): Promise<void> => {
      try {
        const researchAgentStore = useResearchAgentStore();
        if (researchAgentStore.isActive) {
          await researchAgentStore.stopResearch();
        }
      } catch (e) {
        console.error('Failed to stop active research before starting new conversation', e);
      }

      if (activeConversationId.value) {
        updateLatestMessageInConversation(activeConversationId.value, {
          status: 'stopped',
          answer: undefined,
        });
        activeConversation.value = undefined;
      }

      // Create new conversation
      createConversation();
    };

    const clearSearchId = (): void => {
      if (activeConversation.value) {
        activeConversation.value.isSearching = false;
      }
    };

    const createFolder = (name: string): string => {
      const folderId = crypto.randomUUID();
      const newFolder: ConversationFolder = {
        id: folderId,
        name,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      conversationHistory.value.folders.push(newFolder);
      return folderId;
    };

    const updateFolder = (folderId: string, name: string): void => {
      const folder = conversationHistory.value.folders.find((f) => f.id === folderId);
      if (folder) {
        folder.name = name;
        folder.updatedAt = new Date();
      }
    };

    const deleteFolder = (folderId: string): void => {
      conversationHistory.value.savedConversations =
        conversationHistory.value.savedConversations.filter((conv) => conv.folderId !== folderId);

      conversationHistory.value.folders = conversationHistory.value.folders.filter(
        (f) => f.id !== folderId
      );
    };

    const saveConversation = (title?: string, folderId?: string): void => {
      if (!activeConversation.value || activeConversation.value.messages.length === 0) {
        throw new Error('Cannot save empty conversation');
      }

      // Check if this conversation is already saved
      if (isCurrentConversationSaved.value) {
        throw new Error('This conversation is already saved and being auto-updated.');
      }

      const savedConversation = {
        ...activeConversation.value,
        title: title || activeConversation.value.title,
        savedAt: new Date(),
        folderId,
      };

      conversationHistory.value.savedConversations.push(savedConversation);
    };

    const deleteSavedConversation = (savedConversationId: string): void => {
      conversationHistory.value.savedConversations =
        conversationHistory.value.savedConversations.filter(
          (conv) => conv.id !== savedConversationId
        );
    };

    function autoSaveConversationIfPreviouslySaved(): void {
      const savedVersion = currentConversationSavedVersion.value;
      const currentConversation = activeConversation.value;

      if (!savedVersion || !currentConversation) return;

      savedVersion.messages = [...currentConversation.messages]; // Deep copy all messages
      savedVersion.title = currentConversation.title; // Update title in case it changed
      savedVersion.updatedAt = new Date();
    }

    const loadSavedConversation = (savedConversationId: string): void => {
      const savedConversation = conversationHistory.value.savedConversations.find(
        (c) => c.id === savedConversationId
      );
      if (!savedConversation) {
        throw new Error('Saved conversation not found');
      }

      // Clear current conversation
      activeConversation.value = undefined;

      // Create new conversation from saved data
      const newConversation: Conversation = {
        ...savedConversation,
        messages: [...savedConversation.messages], // Deep copy messages
      };

      activeConversation.value = newConversation;
    };

    const canSaveCurrentConversation = computed(() => {
      return activeConversation.value && activeConversation.value.messages.length > 0;
    });

    const currentConversationSavedVersion = computed(() => {
      if (!activeConversation.value) return null;

      return conversationHistory.value.savedConversations.find(
        (saved) => saved.id === activeConversationId.value
      );
    });

    const isCurrentConversationSaved = computed(() => {
      return !!currentConversationSavedVersion.value;
    });

    const savedConversationsByFolder = computed(() => {
      const grouped = conversationHistory.value.savedConversations.reduce(
        (acc, conv) => {
          const folderId = conv.folderId || 'default';
          if (!acc[folderId]) {
            acc[folderId] = [];
          }
          acc[folderId].push(conv);
          return acc;
        },
        {} as Record<string, SavedConversation[]>
      );

      // Sort conversations within each folder by savedAt (newest first)
      Object.keys(grouped).forEach((folderId) => {
        grouped[folderId].sort((a, b) => b.savedAt.getTime() - a.savedAt.getTime());
      });

      return grouped;
    });

    const hasAnyConversations = computed(() => {
      return conversationHistory.value.savedConversations.length > 0;
    });

    const hasAnyFolders = computed(() => {
      return conversationHistory.value.folders.length > 0;
    });

    const hasAnyContent = computed(() => {
      return hasAnyConversations.value || hasAnyFolders.value;
    });

    return {
      // New conversation state
      activeConversationId,
      activeConversation,

      // Conversation history state
      conversationHistory,
      canSaveCurrentConversation,
      isCurrentConversationSaved,
      currentConversationSavedVersion,
      savedConversationsByFolder,
      hasAnyConversations,
      hasAnyFolders,
      hasAnyContent,

      // New conversation methods
      createConversation,
      startNewConversation,
      getOrCreateActiveConversation,
      addMessageToConversation,
      updateMessageInConversation,
      updateLatestMessageInConversation,
      setConversationSearching,

      // Conversation history methods
      createFolder,
      updateFolder,
      deleteFolder,
      saveConversation,
      deleteSavedConversation,
      loadSavedConversation,

      clearSearchId,
    };
  },
  {
    persist: {
      serializer: {
        serialize: (value) => {
          // Convert Date objects to ISO strings for storage
          const serializable = JSON.parse(
            JSON.stringify(value, (key, val) => {
              if (val instanceof Date) {
                return val.toISOString();
              }
              return val;
            })
          );
          return JSON.stringify(serializable);
        },
        deserialize: (value) => {
          // Convert ISO strings back to Date objects
          const parsed = JSON.parse(value);
          return JSON.parse(JSON.stringify(parsed), (key, val) => {
            if (
              typeof val === 'string' &&
              /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/.test(val)
            ) {
              return new Date(val);
            }
            return val;
          });
        },
      },
    },
  }
);

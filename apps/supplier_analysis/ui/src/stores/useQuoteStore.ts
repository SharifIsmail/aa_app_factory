import { createStoreId } from '@/stores/createStoreId.ts';
import { quoteService } from '@/utils/http';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useQuoteStore = defineStore(createStoreId('quote-store'), () => {
  const quoteResponse = ref('');
  const requestIsBeingProcessed = ref(false);

  async function generateQuote() {
    requestIsBeingProcessed.value = true;
    try {
      const response = await quoteService.createQuote();
      quoteResponse.value = response.quote;
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      return undefined;
    } finally {
      requestIsBeingProcessed.value = false;
    }
  }

  return {
    quoteResponse,
    generateQuote,
    requestIsBeingProcessed,
  };
});

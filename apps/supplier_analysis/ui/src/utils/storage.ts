export const STORAGE_KEYS = {
  SEARCH_ID: 'lksg_current_search_id',
};

export const storageUtils = {
  /**
   * Save a search ID to localStorage
   */
  saveSearchId(searchId: string): void {
    localStorage.setItem(STORAGE_KEYS.SEARCH_ID, searchId);
  },

  /**
   * Get the current search ID from localStorage
   */
  getSearchId(): string | null {
    return localStorage.getItem(STORAGE_KEYS.SEARCH_ID);
  },

  /**
   * Clear the current search ID from localStorage
   */
  clearSearchId(): void {
    localStorage.removeItem(STORAGE_KEYS.SEARCH_ID);
  },

  /**
   * Check if there's an active search job
   */
  hasActiveSearch(): boolean {
    return !!this.getSearchId();
  },
};

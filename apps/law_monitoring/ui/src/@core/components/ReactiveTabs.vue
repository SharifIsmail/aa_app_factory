<!--
  ReactiveTabs Component
  
  A fully reactive tab container component that properly handles external prop changes,
  unlike the original AaTabs component which has reactivity issues.
  
  Usage Examples:
  
  1. Simple v-model (Recommended):
     <ReactiveTabs v-model:active-tab="currentTab">
       <AaTab label="Tab 1" name="tab1">Content 1</AaTab>
       <AaTab label="Tab 2" name="tab2">Content 2</AaTab>
     </ReactiveTabs>
  
  2. With custom handler:
     <ReactiveTabs 
       v-model:active-tab="currentTab"
       :handle-tab-click="(tab) => trackTabUsage(tab)"
     >
       <AaTab label="Tab 1" name="tab1">Content 1</AaTab>
     </ReactiveTabs>
  
  3. Manual control:
     <ReactiveTabs 
       :active-tab="currentTab"
       :handle-tab-click="(tab) => setCurrentTab(tab.name)"
     >
       <AaTab label="Tab 1" name="tab1">Content 1</AaTab>
     </ReactiveTabs>
-->

<script setup lang="ts">
import { ref, provide, watch } from 'vue';

/**
 * Tab configuration interface
 */
export interface TabProps {
  /** Unique identifier for the tab */
  name: string;
  /** Display label for the tab */
  label: string;
}

/**
 * Component props interface
 */
export interface ReactiveTabsProps {
  /**
   * Function to run on tab click - optional for additional custom logic
   * @param tab The clicked tab object
   */
  handleTabClick?: (tab: TabProps) => void;

  /**
   * Currently active tab name - supports v-model:active-tab
   * When used with v-model, automatically syncs with parent state
   */
  activeTab?: string;
}

const props = defineProps<ReactiveTabsProps>();

/**
 * Emits for v-model support
 */
const emit = defineEmits<{
  'update:activeTab': [tabName: string];
}>();

// Registry for child tabs that register themselves
const registeredTabs = ref<TabProps[]>([]);

// Internal active tab state - always syncs with external prop
const currentActiveTab = ref(props.activeTab || '');

watch(
  () => props.activeTab,
  (newTab) => {
    if (newTab && newTab !== currentActiveTab.value) {
      currentActiveTab.value = newTab;
    }
  }
);

/**
 * Fallback to first tab if no active tab is set
 */
watch(
  registeredTabs,
  (tabs) => {
    if (tabs.length > 0 && !currentActiveTab.value) {
      currentActiveTab.value = tabs[0].name;
    }
  },
  { immediate: true }
);

/**
 * Register a new tab (called by child AaTab components)
 */
const registerTab = (tab: TabProps) => {
  if (!registeredTabs.value.find((t) => t.name === tab.name)) {
    registeredTabs.value.push(tab);
  }
};

/**
 * Update an existing tab's properties
 */
const updateTab = (tab: TabProps) => {
  registeredTabs.value = registeredTabs.value.map((t) => (t.name === tab.name ? tab : t));
};

/**
 * Handle tab header clicks
 * Updates internal state immediately for responsive UI,
 * emits change for v-model, and calls custom handler if provided
 */
const handleTabClick = (tab: TabProps) => {
  // Update internal state immediately for responsive UI
  currentActiveTab.value = tab.name;

  // Emit the change for v-model support
  emit('update:activeTab', tab.name);

  // Also call legacy handler if provided for custom logic
  if (props.handleTabClick) {
    props.handleTabClick(tab);
  }
};

/**
 * Provide registration functions and active tab state to child components
 * This makes the component compatible with AaTab from @aleph-alpha/ds-components-vue
 */
provide('registerTab', registerTab);
provide('updateTab', updateTab);
provide('activeTab', currentActiveTab);
</script>

<template>
  <div>
    <!-- Tab Headers -->
    <div class="border-b-1 border-core-border-default flex w-fit gap-5">
      <div v-for="tab in registeredTabs" :key="tab.name">
        <button
          :class="[
            'rounded-1 hover:bg-core-bg-tertiary-hover w-full',
            'focus:ring-core-border-focus focus:isolate focus:outline-none focus:ring-2',
            'px -mb-[1px] py-4',
            'z-0',
            currentActiveTab === tab.name
              ? 'label-14-bold color-core-content-accent-soft'
              : 'heading-14 color-core-content-tertiary',
          ]"
          @click="handleTabClick(tab)"
        >
          {{ tab.label }}
        </button>
        <hr
          v-show="currentActiveTab === tab.name"
          class="border-t-1 border-core-content-accent-soft z-1 relative -mb-[1px] w-full"
        />
      </div>
    </div>

    <!-- Tab Content -->
    <slot :active-tab="currentActiveTab" />
  </div>
</template>

<script setup lang="ts">
import MonitoringDashboard from './MonitoringDashboard.vue';
import ReactiveTabs from '@/@core/components/ReactiveTabs.vue';
import { useAppStore } from '@/modules/monitoring/stores/appStore.ts';
import { useLawCoordinatorStore } from '@/modules/monitoring/stores/lawCoordinatorStore';
import { AaTab, AaCircularLoading } from '@aleph-alpha/ds-components-vue';
import { onMounted, nextTick, ref, computed, defineAsyncComponent } from 'vue';

const MonitoringItemized = defineAsyncComponent(() => import('./MonitoringItemized.vue'));

interface Props {
  height: number;
}

const tabsRef = ref<any>();
const tabHeaderHeight = ref(0);
const props = defineProps<Props>();

const appStore = useAppStore();
const lawCoordinatorStore = useLawCoordinatorStore();
const tabContainerHeight = computed(() => props.height - tabHeaderHeight.value);

const measureTabHeaderHeight = async () => {
  await nextTick();
  const container = tabsRef.value?.$el;

  if (container && container.children && container.children.length > 0) {
    const headerElement = container.children[0] as HTMLElement;

    tabHeaderHeight.value = headerElement.offsetHeight;
  }
};

onMounted(async () => {
  await Promise.all([lawCoordinatorStore.fetchAvailableDates(), measureTabHeaderHeight()]);
});
</script>

<template>
  <div class="px-XL flex flex-col" :style="{ height: `${props.height}px` }">
    <!-- Navigation Header -->
    <ReactiveTabs ref="tabsRef" v-model:active-tab="appStore.activeTab">
      <template #default="{ activeTab }">
        <!-- Only render the active tab content -->
        <AaTab label="Dashboard" name="dashboard">
          <div v-if="activeTab === 'dashboard'" class="flex-1 overflow-hidden">
            <MonitoringDashboard :height="tabContainerHeight" />
          </div>
        </AaTab>

        <AaTab label="Itemized" name="list">
          <div v-if="activeTab === 'list'">
            <Suspense>
              <template #default>
                <MonitoringItemized :height="tabContainerHeight" />
              </template>
              <template #fallback>
                <div class="align-flex-start m-t-12 flex gap-2 text-center">
                  <div class="h-8 w-8"><AaCircularLoading /></div>
                  <p class="text-core-content-secondary">Loading itemized view...</p>
                </div>
              </template>
            </Suspense>
          </div>
        </AaTab>
      </template>
    </ReactiveTabs>
  </div>
</template>

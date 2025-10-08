<script setup lang="ts">
import {
  AaAccordion,
  AaAccordionSection,
  AaAccordionTrigger,
  AaAccordionContent,
} from '@aleph-alpha/ds-components-vue';
import { computed } from 'vue';

const props = defineProps<{
  searchStatus: string | null;
  toolLogs: any[];
}>();

const allToolLogsHaveResults = computed(
  () => props.toolLogs.length > 0 && props.toolLogs.every((log) => log.result)
);
</script>

<template>
  <div class="w-full">
    <AaAccordion v-slot="accordionProps">
      <AaAccordionSection id="terminal" :current="accordionProps.current" v-slot="sectionProps">
        <AaAccordionTrigger
          :active="sectionProps.active"
          @click="accordionProps.onToggleItem('terminal')"
        >
          <div class="flex items-center justify-between">
            <span>Research Progress</span>
            <span class="text-xs text-gray-400">
              {{ sectionProps.active ? 'Hide' : 'Show' }} details
            </span>
          </div>
        </AaAccordionTrigger>

        <AaAccordionContent class="max-h-[500px] overflow-y-auto" :active="sectionProps.active">
          <div
            class="terminal-panel h-[500px] w-full rounded-lg bg-gray-800/90 p-4 font-mono text-xs text-gray-400"
          >
            <!-- Display thinking indicator when no tool logs are available but search is in progress -->
            <div
              v-if="(!toolLogs || toolLogs.length === 0) && searchStatus === 'IN_PROGRESS'"
              class="mb-2 mt-1 flex items-baseline"
            >
              <span class="text-gray-500">$</span>
              <span class="ml-1 text-gray-300">{{
                new Date().toLocaleTimeString('en-GB', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                  hour12: false,
                })
              }}</span>
              <span class="text-thinking-blink ml-1 flex items-center">
                <span class="thinking-pulse-dot mr-1.5"></span>
                <span class="font-medium">Thinking</span><span class="dot-1">.</span
                ><span class="dot-2">.</span><span class="dot-3">.</span>
              </span>
            </div>

            <!-- Display tool logs in reverse order -->
            <div v-if="toolLogs && toolLogs.length > 0" class="mt-1 space-y-2">
              <!-- Thinking indicator that appears only when all tool logs have results -->
              <div
                v-if="allToolLogsHaveResults && searchStatus === 'IN_PROGRESS'"
                class="mb-2 mt-1 flex items-baseline"
              >
                <span class="text-gray-500">$</span>
                <span class="ml-1 text-gray-300">{{
                  new Date().toLocaleTimeString('en-GB', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false,
                  })
                }}</span>
                <span class="text-thinking-blink ml-1 flex items-center">
                  <span class="thinking-pulse-dot mr-1.5"></span>
                  <span class="font-medium">Thinking</span><span class="dot-1">.</span
                  ><span class="dot-2">.</span><span class="dot-3">.</span>
                </span>
              </div>

              <div
                v-for="(log, index) in [...toolLogs].reverse()"
                :key="index"
                class="flex flex-col"
              >
                <div :class="['flex items-baseline', !log.result ? 'log-blink-container' : '']">
                  <span class="text-gray-500">$</span>
                  <span class="ml-1 text-gray-300">{{
                    new Date(log.timestamp).toLocaleTimeString('en-GB', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false,
                    })
                  }}</span>
                  <span
                    :class="[
                      'ml-1',
                      !log.result ? 'log-blink-text text-yellow-500' : 'text-yellow-500',
                    ]"
                    >{{ log.tool_name }}</span
                  >
                  <span v-for="(value, key) in log.params" :key="key" class="ml-1">
                    <template v-if="value !== null && value !== undefined && value !== ''">
                      <span class="text-gray-400">--{{ key }}=</span
                      ><span
                        :class="[!log.result ? 'log-blink-text text-teal-500' : 'text-teal-500']"
                        >"{{ value }}"</span
                      >
                    </template>
                  </span>
                </div>

                <!-- Tool result display -->
                <div v-if="log.result" class="relative mb-2 mt-1">
                  <div class="overflow-hidden rounded bg-gray-900/50 p-2">
                    <div class="whitespace-pre-wrap break-words text-xs text-gray-300">
                      {{ log.result }}
                    </div>
                  </div>
                </div>
                <div v-else class="log-loading mb-2 mt-1 pl-5 text-gray-500">
                  <span class="dot-1">.</span><span class="dot-2">.</span
                  ><span class="dot-3">.</span>
                </div>
              </div>
            </div>

            <div class="mt-4 text-gray-500">user@lksg:~$ <span class="blink">_</span></div>
          </div>
        </AaAccordionContent>
      </AaAccordionSection>
    </AaAccordion>
  </div>
</template>

<style scoped>
@keyframes blink {
  50% {
    opacity: 0;
  }
}

.blink {
  animation: blink 1s step-end infinite;
}

.tool-result-ellipsis {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(209, 213, 219, 0.5);
  font-size: 14px;
  height: 15px;
  line-height: 10px;
  pointer-events: none;
}

@keyframes log-blink {
  0%,
  80%,
  100% {
    opacity: 1;
  }
  40% {
    opacity: 0.5;
  }
}

@keyframes dots {
  0%,
  20% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
  60%,
  100% {
    opacity: 0;
  }
}

.log-loading .dot-1 {
  animation: dots 1.5s infinite;
  animation-delay: 0s;
}

.log-loading .dot-2 {
  animation: dots 1.5s infinite;
  animation-delay: 0.3s;
}

.log-loading .dot-3 {
  animation: dots 1.5s infinite;
  animation-delay: 0.6s;
}

.text-thinking-blink {
  color: #d1d5db;
  animation: thinking-blink 2s ease-in-out infinite;
}

@keyframes thinking-blink {
  0%,
  100% {
    opacity: 0.9;
  }
  50% {
    opacity: 0.5;
  }
}

.thinking-pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #60a5fa;
  animation: thinking-pulse 1.5s ease-in-out infinite;
  vertical-align: middle;
}

@keyframes thinking-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 rgba(96, 165, 250, 0);
  }
  50% {
    transform: scale(1.3);
    box-shadow: 0 0 8px rgba(96, 165, 250, 0.7);
  }
}

.terminal-panel {
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(75, 85, 99, 0.8) rgba(55, 65, 81, 0.8);
}

/* WebKit (Chrome, Safari, newer Edge) scrollbar styling */
.terminal-panel::-webkit-scrollbar {
  width: 8px;
  height: 8px;
  background-color: rgba(55, 65, 81, 0.8);
  border-radius: 4px;
}

.terminal-panel::-webkit-scrollbar-thumb {
  background-color: rgba(75, 85, 99, 0.8);
  border-radius: 4px;
  border: 1px solid rgba(55, 65, 81, 0.8);
}

.terminal-panel::-webkit-scrollbar-thumb:hover {
  background-color: rgba(107, 114, 128, 0.9);
}
</style>

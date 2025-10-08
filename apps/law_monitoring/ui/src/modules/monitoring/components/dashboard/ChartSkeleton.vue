<template>
  <div class="chart-skeleton">
    <!-- Simple legend skeleton -->
    <div class="mb-4 flex items-center justify-center gap-4">
      <div class="flex items-center gap-2">
        <div class="h-3 w-3 animate-pulse rounded-full bg-gray-300"></div>
        <div class="h-3 w-16 animate-pulse rounded bg-gray-300"></div>
      </div>
      <div class="flex items-center gap-2">
        <div class="h-3 w-3 animate-pulse rounded-full bg-gray-300"></div>
        <div class="h-3 w-20 animate-pulse rounded bg-gray-300"></div>
      </div>
      <div class="flex items-center gap-2">
        <div class="h-3 w-3 animate-pulse rounded-full bg-gray-300"></div>
        <div class="h-3 w-24 animate-pulse rounded bg-gray-300"></div>
      </div>
    </div>

    <!-- Simple chart area -->
    <div class="flex-1 rounded-lg bg-gray-50 p-4">
      <!-- Chart bars skeleton -->
      <div class="flex h-full items-end justify-between gap-2">
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 60%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 45%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 80%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 35%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 70%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 55%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 90%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 40%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 65%"></div>
        <div class="w-6 animate-pulse rounded-t bg-gray-300" style="height: 75%"></div>
      </div>
    </div>

    <!-- Simple axis labels skeleton -->
    <div class="mt-2 flex justify-between px-4">
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
      <div class="h-2 w-6 animate-pulse rounded bg-gray-300"></div>
    </div>
  </div>
</template>

<style scoped>
.chart-skeleton {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}
</style>

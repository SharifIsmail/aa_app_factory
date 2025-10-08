<script setup lang="ts">
defineOptions({
  name: 'DataSourceDiagram',
});
</script>

<template>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1000" class="h-auto w-full max-w-lg">
    <!-- Background (transparent) -->
    <rect width="1200" height="900" fill="none" />

    <!-- Central AI Agent Circle -->
    <circle
      cx="600"
      cy="500"
      r="100"
      fill="#4052b5"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.8"
    />
    <text
      x="600"
      y="510"
      font-family="Arial"
      font-size="30"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      AI Agent
    </text>

    <!-- Google Search API -->
    <rect
      x="75"
      y="180"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#4285f4"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="225"
      y="265"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Google Search API
    </text>

    <!-- Abstract API (Company Enrich) -->
    <rect
      x="75"
      y="470"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#34a853"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="225"
      y="535"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Company
    </text>
    <text
      x="225"
      y="585"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Enrich API
    </text>

    <!-- OpenCorporates -->
    <rect
      x="75"
      y="760"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#00897b"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="225"
      y="845"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      OpenCorporates
    </text>

    <!-- Worldwide Business Registries -->
    <rect
      x="450"
      y="60"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#673ab7"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="600"
      y="125"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Worldwide
    </text>
    <text
      x="600"
      y="175"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Business Registries
    </text>

    <!-- State Business Registries -->
    <rect
      x="450"
      y="770"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#f4511e"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="600"
      y="835"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      State Business
    </text>
    <text
      x="600"
      y="885"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Registries
    </text>

    <!-- SEC EDGAR -->
    <rect
      x="825"
      y="180"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#ea4335"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="975"
      y="265"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      SEC EDGAR
    </text>

    <!-- European Business Register -->
    <rect
      x="825"
      y="470"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#9c27b0"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="975"
      y="535"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      European
    </text>
    <text
      x="975"
      y="585"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Business Register
    </text>

    <!-- Data.gov -->
    <rect
      x="825"
      y="760"
      width="300"
      height="160"
      rx="25"
      ry="25"
      fill="#0097a7"
      filter="drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.1))"
      opacity="0.75"
    />
    <text
      x="975"
      y="845"
      font-family="Arial"
      font-size="28"
      text-anchor="middle"
      fill="white"
      font-weight="bold"
    >
      Data.gov
    </text>

    <!-- Connection Lines -->
    <line x1="350" y1="265" x2="515" y2="455" stroke="#4285f4" stroke-width="6" opacity="0.6" />
    <line x1="375" y1="550" x2="500" y2="550" stroke="#34a853" stroke-width="6" opacity="0.6" />
    <line x1="350" y1="760" x2="515" y2="545" stroke="#00897b" stroke-width="6" opacity="0.6" />
    <line x1="600" y1="220" x2="600" y2="400" stroke="#673ab7" stroke-width="6" opacity="0.6" />
    <line x1="600" y1="770" x2="600" y2="600" stroke="#f4511e" stroke-width="6" opacity="0.6" />
    <line x1="850" y1="265" x2="685" y2="455" stroke="#ea4335" stroke-width="6" opacity="0.6" />
    <line x1="825" y1="550" x2="700" y2="550" stroke="#9c27b0" stroke-width="6" opacity="0.6" />
    <line x1="850" y1="760" x2="685" y2="545" stroke="#0097a7" stroke-width="6" opacity="0.6" />
  </svg>
</template>

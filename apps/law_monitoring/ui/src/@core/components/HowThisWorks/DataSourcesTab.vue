<script setup lang="ts">
// Template-only component
</script>

<template>
  <div class="space-y-6">
    <div class="text-core-content-primary mb-4 text-xl font-semibold">
      Data Sources and Integrity
    </div>

    <div>
      To provide the best summaries possible, the system uses official and publicly accessible data
      sources.
    </div>

    <div class="flex flex-col space-y-6">
      <div class="flex flex-col space-y-2">
        <div class="text-core-content-primary text-lg font-semibold">Primary Source: EUR-Lex</div>
        <div>
          Our system's main source of legal information is
          <a href="https://eur-lex.europa.eu/" target="_blank" class="text-blue-600 hover:underline"
            >EUR-Lex</a
          >. EUR-Lex is the official online gateway to European Union acts. It provides access to a
          vast collection of legal documents, including:
        </div>
        <ul class="list-disc space-y-1 pl-6">
          <li>Treaties</li>
          <li>Regulations</li>
          <li>Directives</li>
          <li>Decisions</li>
          <li>Consolidated legislation</li>
          <li>Case law</li>
          <li>And more...</li>
        </ul>
        <div>
          By using EUR-Lex, we ensure that the legal texts we analyze are authentic and up-to-date.
        </div>
      </div>

      <div class="flex flex-col space-y-2">
        <div class="text-core-content-primary text-lg font-semibold">
          Focus on Publicly Available Data
        </div>
        <div>
          The system is designed to work with information that is publicly available. It does not
          access private or confidential legal documents.
        </div>
      </div>
    </div>
  </div>
</template>

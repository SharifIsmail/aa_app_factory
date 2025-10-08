<script setup lang="ts">
// Template-only component
</script>

<template>
  <div class="space-y-6">
    <div class="text-core-content-primary mb-4 text-xl font-semibold">The Analysis Process</div>

    <div>
      An automated process is used to generate legal summaries. Here's an outline of the steps
      involved, from the original legal document to the final report:
    </div>

    <div class="flex flex-col space-y-6">
      <div class="flex flex-col space-y-2">
        <div class="text-core-content-primary text-lg font-semibold">Step 1: Act Discovery</div>
        <div>
          The system regularly scans the official European Union legal database (EUR-Lex) to
          identify new acts, regulations, and directives upon their publication.
        </div>
      </div>

      <div class="flex flex-col space-y-2">
        <div class="text-core-content-primary text-lg font-semibold">
          Step 2: Full Text Retrieval
        </div>
        <div>
          Once a new or relevant legal document is identified, its complete text is retrieved to
          ensure the analysis is based on the official and comprehensive wording.
        </div>
      </div>

      <div class="flex flex-col space-y-2">
        <div class="text-core-content-primary text-lg font-semibold">
          Step 3: AI-Powered Analysis
        </div>
        <div>
          The retrieved legal text is processed by an AI model. This AI is designed to interpret
          legal language and extract key information, such as:
        </div>
        <ul class="mt-2 list-disc space-y-1 pl-6">
          <li>
            <span class="font-semibold">Subject Matter:</span> The primary topics and areas covered
            by the act.
          </li>
          <li>
            <span class="font-semibold">Timeline and Deadlines:</span> Effective dates and any
            important compliance deadlines.
          </li>
          <li>
            <span class="font-semibold">Roles and Responsibilities:</span> Entities affected by the
            act and their specific duties.
          </li>
          <li>
            <span class="font-semibold">Penalties and Consequences:</span> Stated outcomes for
            non-compliance, including fines or other penalties.
          </li>
        </ul>
      </div>

      <div class="flex flex-col space-y-2">
        <div class="text-core-content-primary text-lg font-semibold">
          Step 4: Summary Report Generation
        </div>
        <div>
          Following the AI analysis, the extracted information is compiled into a structured report.
          This report highlights the key findings to provide an accessible overview of the act.
        </div>
      </div>
    </div>
  </div>
</template>

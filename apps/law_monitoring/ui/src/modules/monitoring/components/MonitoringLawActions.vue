<script setup lang="ts">
import { useApplicationConfigStore } from '@/@core/stores/applicationConfigStore';
import { type PreprocessedLaw } from '@/modules/monitoring/types';
import { AaButton } from '@aleph-alpha/ds-components-vue';

interface Props {
  law: PreprocessedLaw;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'open-full-report': [law: PreprocessedLaw];
  'download-pdf-report': [law: PreprocessedLaw];
  'download-word-report': [law: PreprocessedLaw];
}>();

const applicationConfigStore = useApplicationConfigStore();

function openPwcEmail(law: PreprocessedLaw) {
  const subject = encodeURIComponent(`Inquiry about law: ${law.title}`);
  const body = encodeURIComponent(
    `Hello PwC Team,

I have a question regarding the following law:

Series: ${law.oj_series_label}
Type: ${law.document_type_label}
Title: ${law.title}

URL: ${law.pdf_url}

Please reach out to me to arrange for getting your insights and support regarding this law.

Thank you!`
  );
  const mailto = `mailto:law-monitoring@pwc.com?subject=${subject}&body=${body}`;
  window.open(mailto, '_blank');
}
</script>

<template>
  <div>
    <AaButton
      v-if="applicationConfigStore.applicationConfig.enable_engage_partner_button"
      variant="primary"
      @click="openPwcEmail(props.law)"
      prepend-icon="i-material-symbols-support-agent"
    >
      Reach out to PwC
    </AaButton>
    <AaButton
      variant="outline"
      :disabled="law.status !== 'PROCESSED'"
      @click="emit('open-full-report', props.law)"
      prepend-icon="i-material-symbols-open-in-new"
    >
      See Full Report
    </AaButton>
    <AaButton
      variant="outline"
      :disabled="law.status !== 'PROCESSED'"
      @click="emit('download-pdf-report', props.law)"
      prepend-icon="i-material-symbols-download"
    >
      Download PDF
    </AaButton>
    <AaButton
      variant="outline"
      :disabled="law.status !== 'PROCESSED'"
      @click="emit('download-word-report', props.law)"
      prepend-icon="i-material-symbols-download"
    >
      Download DOC
    </AaButton>
    <AaButton
      :href="law.pdf_url"
      target="_blank"
      variant="outline"
      prepend-icon="i-material-symbols-open-in-new"
    >
      Show Full Legal Act
    </AaButton>
  </div>
</template>

<script setup lang="ts">
import { useCompanyConfigStore } from '@/@core/stores/companyConfigStore';
import type { TeamDescription } from '@/@core/types/companyConfig';
import { AaButton, AaInput, AaModal, AaText } from '@aleph-alpha/ds-components-vue';
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  editingTeam: TeamDescription | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const companyStore = useCompanyConfigStore();

const teamForm = ref<TeamDescription>({
  name: '',
  description: '',
  department: '',
  daily_processes: [],
  relevant_laws_or_topics: '',
});

// Store original team name for edit operations
const originalTeamName = ref<string>('');

// Daily processes input (comma-separated)
const dailyProcessesInput = ref('');

// Computed properties
const isFormValid = computed(() => {
  return (
    teamForm.value.name.trim() &&
    teamForm.value.description.trim() &&
    teamForm.value.department.trim()
  );
});

const modalTitle = computed(() => {
  return props.editingTeam ? 'Edit Team' : 'Add New Team';
});

const submitButtonText = computed(() => {
  return props.editingTeam ? 'Update' : 'Add';
});

const isEditMode = computed(() => !!props.editingTeam);

// Initialize form when editing team changes
watch(
  () => props.editingTeam,
  (team) => {
    if (team) {
      teamForm.value = { ...team };
      originalTeamName.value = team.name; // Store original name
      dailyProcessesInput.value = team.daily_processes.join(', ');
    } else {
      teamForm.value = {
        name: '',
        description: '',
        department: '',
        daily_processes: [],
        relevant_laws_or_topics: '',
      };
      originalTeamName.value = '';
      dailyProcessesInput.value = '';
    }
  },
  { immediate: true }
);

const saveTeam = async () => {
  if (!isFormValid.value) return;

  // Parse daily processes from comma-separated input
  const dailyProcesses = dailyProcessesInput.value
    .split(',')
    .map((process) => process.trim())
    .filter((process) => process.length > 0);

  const teamToSave: TeamDescription = {
    ...teamForm.value,
    daily_processes: dailyProcesses,
  };

  // Use different methods for add vs edit operations
  if (isEditMode.value) {
    await companyStore.updateTeam(originalTeamName.value, teamToSave);
  } else {
    await companyStore.addTeam(teamToSave);
  }

  emit('close');
};
</script>

<template>
  <AaModal :title="modalTitle" with-overlay @close="emit('close')">
    <div class="flex w-[600px] flex-col overflow-hidden">
      <div class="flex-1 overflow-y-auto p-6">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col">
              <AaText weight="bold" size="sm" class="pb-1"> Team Name </AaText>
              <AaInput
                v-model="teamForm.name"
                label="Team Name"
                name="Team Name"
                placeholder="Enter the name of the team..."
              />
            </div>
            <div class="flex flex-col">
              <AaText weight="bold" size="sm" class="pb-1"> Department </AaText>
              <AaInput
                v-model="teamForm.department"
                label="Department"
                placeholder="Enter the department of the team..."
              />
            </div>
          </div>

          <div>
            <AaText weight="bold" size="sm" class="pb-1"> Description </AaText>
            <textarea
              v-model="teamForm.description"
              aria-label="Description"
              placeholder="Brief description of the team's role and responsibilities..."
              class="border-1 bg-core-bg-primary focus-within:ring-core-border-focus placeholder-core-content-placeholder color-core-content-secondary border-core-border-default enabled:hover:border-core-border-hover focus-within:border-core-content-secondary flex w-full appearance-none items-center rounded px-3 py-1 outline-none focus-within:ring-2 disabled:opacity-40"
              rows="3"
            />
          </div>

          <div>
            <AaText weight="bold" size="sm" class="pb-1"> Daily Processes (optional) </AaText>
            <textarea
              v-model="dailyProcessesInput"
              aria-label="Daily Processes"
              placeholder="Enter typical daily processes of this team (comma-separated)..."
              class="border-1 bg-core-bg-primary focus-within:ring-core-border-focus placeholder-core-content-placeholder color-core-content-secondary border-core-border-default enabled:hover:border-core-border-hover focus-within:border-core-content-secondary flex w-full appearance-none items-center rounded px-3 py-1 outline-none focus-within:ring-2 disabled:opacity-40"
              rows="2"
            />
          </div>

          <div>
            <AaText weight="bold" size="sm" class="pb-1">
              Relevant Laws or Topics (optional)
            </AaText>
            <textarea
              v-model="teamForm.relevant_laws_or_topics"
              placeholder="Enter legal areas or topics relevant to this team..."
              class="border-1 bg-core-bg-primary focus-within:ring-core-border-focus placeholder-core-content-placeholder color-core-content-secondary border-core-border-default enabled:hover:border-core-border-hover focus-within:border-core-content-secondary flex w-full appearance-none items-center rounded px-3 py-1 outline-none focus-within:ring-2 disabled:opacity-40"
              rows="2"
            />
          </div>

          <div class="flex gap-2 pt-4">
            <AaButton
              variant="primary"
              size="medium"
              @click="saveTeam"
              :disabled="!isFormValid || companyStore.isUpdating"
              :loading="companyStore.isUpdating"
            >
              {{ submitButtonText }} Team
            </AaButton>
            <AaButton
              variant="outline"
              size="medium"
              @click="emit('close')"
              :disabled="companyStore.isUpdating"
            >
              Cancel
            </AaButton>
          </div>
        </div>
      </div>
    </div>
  </AaModal>
</template>

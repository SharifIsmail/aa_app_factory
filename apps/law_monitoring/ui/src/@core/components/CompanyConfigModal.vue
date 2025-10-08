<script setup lang="ts">
import CompanyConfigAddTeamModal from '@/@core/components/CompanyConfigAddTeamModal.vue';
import { useCompanyConfigStore } from '@/@core/stores/companyConfigStore';
import type { TeamDescription } from '@/@core/types/companyConfig';
import { AaButton, AaModal, AaSmallBanner, AaText } from '@aleph-alpha/ds-components-vue';
import { computed, onMounted, ref } from 'vue';

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const companyStore = useCompanyConfigStore();

const companyDescription = ref('');
const originalCompanyDescription = ref('');

// Modal state
const showCompanyModal = ref(true);
const showTeamForm = ref(false);
const editingTeam = ref<TeamDescription | null>(null);
const showInfoBanner = ref(true);

// Computed properties
const hasDescriptionChanged = computed(() => {
  return companyDescription.value !== originalCompanyDescription.value;
});

// Common table header styles
const commonHeaderClasses = 'border px-4 py-2 text-left text-sm';

// Initialize data
onMounted(async () => {
  await companyStore.fetchCompanyConfig();
  const description = companyStore.companyConfig.company_description || '';
  companyDescription.value = description;
  originalCompanyDescription.value = description;
});

// Company description methods
const cancelEditingDescription = () => {
  companyDescription.value = originalCompanyDescription.value;
};

const saveCompanyDescription = async () => {
  if (!companyDescription.value.trim()) return;

  await companyStore.saveCompanyDescription(companyDescription.value.trim());
  originalCompanyDescription.value = companyDescription.value;
};

// Modal management methods
const closeCompanyModal = () => {
  showCompanyModal.value = false;
  emit('close');
};

const closeBanner = () => {
  showInfoBanner.value = false;
};

// Team management methods
const openTeamForm = (team?: TeamDescription) => {
  if (team) {
    editingTeam.value = team;
  } else {
    editingTeam.value = null;
  }
  showCompanyModal.value = false; // Close company modal
  showTeamForm.value = true;
};

const closeTeamForm = () => {
  showTeamForm.value = false;
  editingTeam.value = null;
  showCompanyModal.value = true; // Reopen company modal
};

const deleteTeam = async (teamName: string) => {
  if (confirm(`Are you sure you want to delete the team "${teamName}"?`)) {
    await companyStore.deleteTeam(teamName);
  }
};
</script>

<template>
  <Teleport to="body">
    <!-- Company Configuration Modal -->
    <AaModal
      v-if="showCompanyModal"
      title="Company Settings"
      with-overlay
      @close="closeCompanyModal"
    >
      <div class="flex h-[70vh] w-[80vw] max-w-5xl flex-col overflow-y-scroll">
        <div class="w-[90%] self-center pr-8">
          <AaSmallBanner
            v-if="showInfoBanner"
            class="m-4"
            :soft="true"
            variant="info"
            @close="closeBanner"
          >
            Please note that adding or editing the company information will only affect the analysis
            of all legal acts that are processed in the future. Already analyzed legal acts will not
            be reprocessed to reflect the changes made in company description and team structure.
          </AaSmallBanner>
        </div>
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-8">
            <!-- Company Description Section -->
            <div class="space-y-4">
              <AaText class="text-core-content-primary" weight="bold" size="lg">
                Company Description
              </AaText>

              <div class="space-y-3">
                <textarea
                  aria-label="Company Description"
                  v-model="companyDescription"
                  placeholder="Enter company description..."
                  class="border-1 bg-core-bg-primary focus-within:ring-core-border-focus placeholder-core-content-placeholder color-core-content-secondary border-core-border-default enabled:hover:border-core-border-hover focus-within:border-core-content-secondary flex w-full appearance-none items-center rounded px-3 py-1 outline-none focus-within:ring-2 disabled:opacity-40"
                />
                <div class="flex gap-2">
                  <AaButton
                    variant="primary"
                    size="medium"
                    @click="saveCompanyDescription"
                    :disabled="
                      companyStore.isUpdating ||
                      !companyDescription.trim() ||
                      !hasDescriptionChanged
                    "
                    :loading="companyStore.isUpdating"
                  >
                    Save
                  </AaButton>
                  <AaButton
                    variant="outline"
                    size="medium"
                    @click="cancelEditingDescription"
                    :disabled="companyStore.isUpdating || !hasDescriptionChanged"
                  >
                    Cancel
                  </AaButton>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <AaText class="text-core-content-primary" size="lg" weight="bold"> Teams</AaText>
                <AaButton
                  variant="secondary"
                  size="medium"
                  prepend-icon="i-material-symbols-add"
                  @click="openTeamForm()"
                  :disabled="companyStore.isLoading"
                >
                  Add Team
                </AaButton>
              </div>

              <!-- Teams Table -->
              <div v-if="companyStore.teamsSorted.length > 0" class="overflow-hidden rounded-md">
                <table class="w-full table-auto">
                  <thead>
                    <tr class="bg-core-bg-secondary text-core-content-primary border">
                      <th :class="[commonHeaderClasses, 'w-48']">Name</th>
                      <th :class="[commonHeaderClasses, 'w-40']">Department</th>
                      <th :class="commonHeaderClasses">Description</th>
                      <th :class="[commonHeaderClasses, 'w-32']">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="team in companyStore.teamsSorted"
                      :key="team.name"
                      class="hover:bg-gray-50"
                    >
                      <td
                        class="text-core-content-primary w-48 border px-4 py-2 text-sm font-medium"
                      >
                        {{ team.name }}
                      </td>
                      <td class="text-core-content-secondary w-40 border px-4 py-2 text-sm">
                        {{ team.department }}
                      </td>
                      <td class="text-core-content-secondary border px-4 py-2 text-sm">
                        <div :title="team.description">
                          {{ team.description }}
                        </div>
                      </td>
                      <td class="w-32 border px-4 py-2 text-right">
                        <div class="flex justify-end gap-1">
                          <AaButton
                            variant="outline"
                            size="small"
                            prepend-icon="i-material-symbols-edit-outline"
                            @click="openTeamForm(team)"
                            :disabled="companyStore.isUpdating"
                          >
                            Edit
                          </AaButton>
                          <AaButton
                            variant="danger"
                            size="small"
                            prepend-icon="i-material-symbols-delete-outline"
                            @click="deleteTeam(team.name)"
                            :disabled="companyStore.isUpdating"
                          >
                            Delete
                          </AaButton>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-else-if="!companyStore.isLoading" class="py-8 text-center text-gray-500">
                <p>No teams configured yet.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AaModal>

    <!-- Team Form Modal -->
    <CompanyConfigAddTeamModal
      v-if="showTeamForm"
      :editing-team="editingTeam"
      @close="closeTeamForm"
    />
  </Teleport>
</template>

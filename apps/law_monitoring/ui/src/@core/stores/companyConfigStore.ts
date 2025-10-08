import { createStoreId } from '@/@core/stores/createStoreId';
import { useNotificationStore } from '@/@core/stores/useNotificationStore';
import type { CompanyConfig, TeamDescription } from '@/@core/types/companyConfig';
import { companyConfigService } from '@/@core/utils/http';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export const useCompanyConfigStore = defineStore(createStoreId('company-config'), () => {
  const notificationStore = useNotificationStore();

  const companyConfig = ref<CompanyConfig>({
    company_description: null,
    teams: [],
  });

  const isLoading = ref(false);
  const isUpdating = ref(false);

  const hasCompanyDescription = computed(() => !!companyConfig.value.company_description);

  const teamsSorted = computed(() =>
    [...companyConfig.value.teams].sort((a, b) => a.name.localeCompare(b.name))
  );

  const getTeamByName = computed(
    () => (name: string) =>
      companyConfig.value.teams.find((team) => team.name.toLowerCase() === name.toLowerCase())
  );

  const departmentOptions = computed(() => {
    const departments = new Set<string>();

    for (const team of companyConfig.value.teams) {
      if (team.department && team.department.trim()) {
        departments.add(team.department.trim());
      }
    }

    return Array.from(departments)
      .sort()
      .map((dept) => ({
        value: dept,
        label: dept,
      }));
  });

  async function fetchCompanyConfig(): Promise<void> {
    try {
      isLoading.value = true;
      const config = await companyConfigService.getCompanyConfig();

      companyConfig.value.company_description = config.company_description;
      companyConfig.value.teams = config.teams;
    } catch (error) {
      console.error('Failed to fetch company configuration:', error);
      notificationStore.addErrorNotification(
        'Failed to load company configuration. Please try again.'
      );
    } finally {
      isLoading.value = false;
    }
  }

  async function saveCompanyDescription(description: string): Promise<void> {
    const originalDescription = companyConfig.value.company_description;

    try {
      isUpdating.value = true;

      // Optimistic update
      companyConfig.value.company_description = description;

      companyConfig.value.company_description =
        await companyConfigService.updateCompanyDescription(description);

      notificationStore.addSuccessNotification('Company description updated successfully.');
    } catch (error) {
      console.error('Failed to update company description:', error);

      // Rollback optimistic update
      companyConfig.value.company_description = originalDescription;

      notificationStore.addErrorNotification(
        'Failed to update company description. Please try again.'
      );
    } finally {
      isUpdating.value = false;
    }
  }

  async function addTeam(team: TeamDescription): Promise<void> {
    // Check if team already exists to prevent duplicates
    const existingTeamIndex = companyConfig.value.teams.findIndex(
      (t) => t.name.toLowerCase() === team.name.toLowerCase()
    );

    if (existingTeamIndex >= 0) {
      notificationStore.addErrorNotification(
        `Team "${team.name}" already exists. Please use a different name.`
      );
      return;
    }

    const originalTeams = [...companyConfig.value.teams];

    try {
      isUpdating.value = true;

      // Optimistic update - only add, don't update
      companyConfig.value.teams.push(team);

      const savedTeam = await companyConfigService.addTeam(team);

      // Update with server response
      const newTeamIndex = companyConfig.value.teams.findIndex(
        (t) => t.name.toLowerCase() === team.name.toLowerCase()
      );
      if (newTeamIndex >= 0) {
        companyConfig.value.teams[newTeamIndex] = savedTeam;
      }

      notificationStore.addSuccessNotification(`Team "${savedTeam.name}" added successfully.`);
    } catch (error) {
      console.error('Failed to add team:', error);

      // Rollback optimistic update
      companyConfig.value.teams = originalTeams;

      notificationStore.addErrorNotification('Failed to add team. Please try again.');
    } finally {
      isUpdating.value = false;
    }
  }

  async function updateTeam(teamName: string, team: TeamDescription): Promise<void> {
    const teamIndex = companyConfig.value.teams.findIndex(
      (t) => t.name.toLowerCase() === teamName.toLowerCase()
    );

    if (teamIndex === -1) {
      notificationStore.addErrorNotification(`Team "${teamName}" not found.`);
      return;
    }

    const originalTeam = companyConfig.value.teams[teamIndex];

    try {
      isUpdating.value = true;

      // Optimistic update
      companyConfig.value.teams[teamIndex] = team;

      const savedTeam = await companyConfigService.updateTeam(teamName, team);
      companyConfig.value.teams[teamIndex] = savedTeam;

      notificationStore.addSuccessNotification(`Team "${savedTeam.name}" updated successfully.`);
    } catch (error) {
      console.error('Failed to update team:', error);

      // Rollback optimistic update
      companyConfig.value.teams[teamIndex] = originalTeam;

      notificationStore.addErrorNotification('Failed to update team. Please try again.');
    } finally {
      isUpdating.value = false;
    }
  }

  async function deleteTeam(teamName: string): Promise<void> {
    const teamIndex = companyConfig.value.teams.findIndex(
      (t) => t.name.toLowerCase() === teamName.toLowerCase()
    );

    if (teamIndex === -1) {
      notificationStore.addErrorNotification(`Team "${teamName}" not found.`);
      return;
    }

    const originalTeams = [...companyConfig.value.teams];

    try {
      isUpdating.value = true;

      // Optimistic update
      companyConfig.value.teams.splice(teamIndex, 1);

      await companyConfigService.deleteTeam(teamName);

      notificationStore.addSuccessNotification(`Team "${teamName}" deleted successfully.`);
    } catch (error) {
      console.error('Failed to delete team:', error);

      // Rollback optimistic update
      companyConfig.value.teams = originalTeams;

      notificationStore.addErrorNotification('Failed to delete team. Please try again.');
    } finally {
      isUpdating.value = false;
    }
  }

  return {
    companyConfig,
    isLoading,
    isUpdating,
    hasCompanyDescription,
    teamsSorted,
    getTeamByName,
    departmentOptions,
    fetchCompanyConfig,
    saveCompanyDescription,
    addTeam,
    updateTeam,
    deleteTeam,
  };
});

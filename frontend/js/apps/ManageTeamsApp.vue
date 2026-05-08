<script setup>
import { ref, computed, onMounted } from 'vue';
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';
import { get, post, patch, del, parseErrors } from '../utils/api';
import { showToast } from '../composables/useToast';
import { userFullName } from '../utils/format';
import AppModal from '../components/AppModal.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import AppListCard from '../components/AppListCard.vue';
import ComboboxTagsInput from '../components/ComboboxTagsInput.vue';
import UserAvatar from '../components/UserAvatar.vue';
import UserBadge from '../components/UserBadge.vue';

const props = defineProps({
  teamListUrl: { type: String, required: true },
  organizationMemberListUrl: { type: String, required: true },
});

const teams = ref([]);
const memberOptions = ref([]);
const confirmRef = ref(null);

const modalOpen = ref(false);
const modalTitle = ref('Add Team');
const editingTeam = ref(null);
const formName = ref('');
const formMembers = ref([]);
const formErrors = ref({});

const memberOptionsList = computed(() =>
  memberOptions.value.map((m) => ({
    value: String(m.id),
    label: userFullName(m) || m.username,
  })),
);

async function loadTeams() {
  try {
    const data = await get(props.teamListUrl);
    teams.value = data.results || data;
  } catch {
    showToast('Failed to load teams.', 'error');
  }
}

async function loadMembers() {
  try {
    const data = await get(props.organizationMemberListUrl);
    const results = data.results || data;
    memberOptions.value = results.map((m) => m.user || m);
  } catch {
    memberOptions.value = [];
  }
}

function openModal(team = null) {
  formErrors.value = {};
  if (team) {
    modalTitle.value = 'Edit Team';
    editingTeam.value = team;
    formName.value = team.name;
    formMembers.value = (team.member_details || []).map((m) => String(m.id));
  } else {
    modalTitle.value = 'Add Team';
    editingTeam.value = null;
    formName.value = '';
    formMembers.value = [];
  }
  modalOpen.value = true;
}

function closeModal() {
  modalOpen.value = false;
}

async function saveTeam() {
  const name = formName.value.trim();
  if (!name) {
    formErrors.value = { name: ['Name is required.'] };
    return;
  }
  const payload = {
    name,
    members: formMembers.value.map(Number),
  };
  try {
    if (editingTeam.value) {
      await patch(`${props.teamListUrl}${editingTeam.value.id}/`, payload);
      showToast('Team updated.');
    } else {
      await post(props.teamListUrl, payload);
      showToast('Team created.');
    }
    modalOpen.value = false;
    await loadTeams();
  } catch (err) {
    formErrors.value = parseErrors(err);
  }
}

async function deleteTeam(team) {
  const confirmed = await confirmRef.value.confirm(`Are you sure you want to delete "${team.name}"?`, 'Delete Team');
  if (!confirmed) return;
  try {
    await del(`${props.teamListUrl}${team.id}/`);
    showToast('Team deleted.');
    await loadTeams();
  } catch {
    showToast('Failed to delete team.', 'error');
  }
}

onMounted(() => {
  loadTeams();
  loadMembers();
});
</script>

<template>
  <div>
    <div class="flex justify-end mb-4">
      <button
        class="cursor-pointer inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        @click="openModal()"
      >
        <PlusIcon class="h-4 w-4" />
        Add Team
      </button>
    </div>

    <AppListCard>
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Name
            </th>
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Members
            </th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="team in teams"
            :key="team.id"
            class="group border-b border-gray-100 transition-colors hover:bg-gray-50 dark:border-gray-700/50 dark:hover:bg-gray-800/30"
          >
            <td class="px-4 py-3">
              <span class="text-gray-900 dark:text-white">{{ team.name }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-700 dark:text-gray-300">
                <template v-if="(team.member_details || []).length === 1">
                  <UserBadge :user="team.member_details[0]" truncate />
                </template>
                <template v-else-if="(team.member_details || []).length > 1">
                  <div class="flex items-center -space-x-1">
                    <UserAvatar
                      v-for="member in team.member_details.slice(0, 3)"
                      :key="member.id"
                      :src="member.avatar_url || ''"
                      :name="userFullName(member)"
                      size="sm"
                      :title="userFullName(member)"
                      class="ring-2 ring-white dark:ring-gray-900"
                    />
                    <span
                      v-if="team.member_details.length > 3"
                      class="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gray-200 text-[10px] font-medium text-gray-700 ring-2 ring-white dark:bg-gray-700 dark:text-gray-300 dark:ring-gray-900"
                      :title="
                        team.member_details
                          .slice(3)
                          .map((m) => userFullName(m))
                          .join(', ')
                      "
                      >+{{ team.member_details.length - 3 }}</span
                    >
                  </div>
                </template>
                <span v-else class="text-sm text-gray-400 dark:text-gray-500"> No members </span>
              </div>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  class="cursor-pointer inline-flex items-center rounded p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-300"
                  title="Edit"
                  @click="openModal(team)"
                >
                  <PencilIcon class="h-4 w-4" />
                </button>
                <button
                  class="cursor-pointer inline-flex items-center rounded p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                  title="Delete"
                  @click="deleteTeam(team)"
                >
                  <TrashIcon class="h-4 w-4" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="teams.length === 0">
            <td colspan="3" class="py-12 text-center text-gray-500 dark:text-gray-400">No teams found.</td>
          </tr>
        </tbody>
      </table>
    </AppListCard>

    <!-- Create / Edit Modal -->
    <AppModal :open="modalOpen" :title="modalTitle" @close="closeModal">
      <div class="mb-4">
        <label for="team-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
        <input
          id="team-name"
          v-model="formName"
          type="text"
          class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          @keyup.enter="saveTeam"
        />
        <p v-if="formErrors.name" class="mt-1 text-sm text-red-600">
          {{ formErrors.name.join(' ') }}
        </p>
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Members</label>
        <ComboboxTagsInput v-model="formMembers" :options="memberOptionsList" placeholder="Add members..." />
        <p v-if="formErrors.members" class="mt-1 text-sm text-red-600">
          {{ formErrors.members.join(' ') }}
        </p>
      </div>
      <p v-if="formErrors.non_field_errors" class="mb-4 text-sm text-red-600">
        {{ formErrors.non_field_errors.join(' ') }}
      </p>
      <template #footer>
        <button
          class="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
          @click="closeModal"
        >
          Cancel
        </button>
        <button
          class="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          @click="saveTeam"
        >
          {{ editingTeam ? 'Update' : 'Save' }}
        </button>
      </template>
    </AppModal>

    <ConfirmModal ref="confirmRef" />
  </div>
</template>

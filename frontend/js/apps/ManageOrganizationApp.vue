<script setup>
import { ref, onMounted } from 'vue';
import { ArrowPathIcon, UserMinusIcon, EnvelopeIcon, XMarkIcon } from '@heroicons/vue/24/outline';
import { get, post, patch, del, parseErrors } from '../utils/api';
import { showToast } from '../composables/useToast';
import { userFullName } from '../utils/format';
import AppModal from '../components/AppModal.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import UserAvatar from '../components/UserAvatar.vue';
import UserBadge from '../components/UserBadge.vue';

const props = defineProps({
  orgName: { type: String, required: true },
  organizationMemberListUrl: { type: String, required: true },
  organizationInviteListUrl: { type: String, required: true },
  currentUserId: { type: Number, required: true },
});

const members = ref([]);
const invites = ref([]);
const searchQuery = ref('');
const searchResults = ref([]);
const inviteEmailModalOpen = ref(false);
const inviteEmail = ref('');
const inviteEmailError = ref('');
const confirmRef = ref(null);
let searchTimeout = null;

async function loadData() {
  try {
    const [membersData, invitesData] = await Promise.all([
      get(props.organizationMemberListUrl),
      get(props.organizationInviteListUrl),
    ]);
    members.value = membersData.results || membersData;
    invites.value = invitesData.results || invitesData;
  } catch {
    showToast('Failed to load data.', 'error');
  }
}

async function searchUsers(query) {
  try {
    const data = await get(`${props.organizationMemberListUrl}search/`, { q: query });
    searchResults.value = data || [];
  } catch {
    showToast('Search failed.', 'error');
  }
}

function onSearchInput(e) {
  clearTimeout(searchTimeout);
  const query = e.target.value.trim();
  if (query.length < 3) {
    searchResults.value = [];
    return;
  }
  searchTimeout = setTimeout(() => searchUsers(query), 300);
}

async function inviteUser(userId) {
  try {
    await post(props.organizationInviteListUrl, { invitee: userId });
    showToast('Invitation sent.');
    searchQuery.value = '';
    searchResults.value = [];
    await loadData();
  } catch (err) {
    const errors = parseErrors(err);
    showToast(Object.values(errors).flat().join(' '), 'error');
  }
}

function openInviteByEmailModal() {
  inviteEmail.value = '';
  inviteEmailError.value = '';
  inviteEmailModalOpen.value = true;
}

async function sendEmailInvite() {
  const email = inviteEmail.value.trim();
  if (!email) {
    inviteEmailError.value = 'Email is required.';
    return;
  }
  try {
    await post(props.organizationInviteListUrl, { invitee_email: email });
    inviteEmailModalOpen.value = false;
    showToast('Invitation sent.');
    await loadData();
  } catch (err) {
    const errors = parseErrors(err);
    inviteEmailError.value = Object.values(errors).flat().join(' ');
  }
}

async function changeRole(member) {
  const user = member.user || member;
  const currentRole = member.is_owner ? 'owner' : 'member';
  const newRole = member.is_owner ? 'member' : 'owner';
  const confirmed = await confirmRef.value.confirm(
    `Change ${userFullName(user)}'s role from ${currentRole} to ${newRole}?`,
    'Change Role',
  );
  if (!confirmed) return;
  try {
    await patch(`${props.organizationMemberListUrl}${member.pk}/`, { is_owner: !member.is_owner });
    showToast('Role updated.');
    await loadData();
  } catch {
    showToast('Failed to change role.', 'error');
  }
}

async function removeMember(member) {
  const user = member.user || member;
  const confirmed = await confirmRef.value.confirm(
    `Remove ${userFullName(user)} from ${props.orgName}?`,
    'Remove Member',
  );
  if (!confirmed) return;
  try {
    await del(`${props.organizationMemberListUrl}${member.pk}/`);
    showToast('Member removed.');
    await loadData();
  } catch {
    showToast('Failed to remove member.', 'error');
  }
}

async function cancelInvite(invite) {
  const confirmed = await confirmRef.value.confirm('Cancel this invitation?', 'Cancel Invite');
  if (!confirmed) return;
  try {
    await del(`${props.organizationInviteListUrl}${invite.pk}/`);
    showToast('Invitation cancelled.');
    await loadData();
  } catch {
    showToast('Failed to cancel invitation.', 'error');
  }
}

onMounted(loadData);
</script>

<template>
  <div>
    <!-- Members -->
    <div class="mb-6">
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th class="pb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Name</th>
            <th class="pb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Email</th>
            <th class="pb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Role</th>
            <th class="pb-2" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in members" :key="member.pk" class="border-b border-gray-100 dark:border-gray-700">
            <td class="py-2 text-gray-900 dark:text-white">
              <UserBadge :user="member.user || member" fallback="icon" />
            </td>
            <td class="py-2 text-gray-700 dark:text-gray-300">
              {{ (member.user || member).email || (member.user || member).username || '' }}
            </td>
            <td class="py-2">
              <span
                :class="[
                  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                  member.is_owner
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
                ]"
              >
                {{ member.is_owner ? 'owner' : 'member' }}
              </span>
            </td>
            <td class="py-2 text-right">
              <button
                :disabled="(member.user || member).id === currentUserId"
                class="cursor-pointer inline-flex items-center gap-1 rounded p-1.5 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed dark:hover:bg-gray-700 dark:hover:text-gray-300"
                title="Change Role"
                @click="changeRole(member)"
              >
                <ArrowPathIcon class="h-4 w-4" />
                Change Role
              </button>
              <button
                :disabled="(member.user || member).id === currentUserId"
                class="cursor-pointer inline-flex items-center rounded p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-600 disabled:opacity-50 disabled:cursor-not-allowed dark:hover:bg-red-900/20 dark:hover:text-red-400"
                title="Remove"
                @click="removeMember(member)"
              >
                <UserMinusIcon class="h-4 w-4" />
              </button>
            </td>
          </tr>
          <tr v-if="members.length === 0">
            <td colspan="4" class="py-4 text-center text-gray-500 dark:text-gray-400">No members.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Invite -->
    <div class="mb-6">
      <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Invite a Member</h4>
      <div class="flex gap-2 mb-2 max-w-lg">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by name, email, or username..."
          class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          @input="onSearchInput"
        />
        <button
          class="cursor-pointer inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="openInviteByEmailModal"
        >
          <EnvelopeIcon class="h-4 w-4" />
          Invite by Email
        </button>
      </div>
      <div v-if="searchResults.length > 0" class="max-w-lg border border-gray-200 rounded-md dark:border-gray-700">
        <button
          v-for="result in searchResults"
          :key="result.pk"
          class="cursor-pointer flex items-center gap-2 w-full text-left px-3 py-2 text-sm hover:bg-gray-100 border-b border-gray-100 last:border-0 dark:hover:bg-gray-700 dark:text-gray-300 dark:border-gray-700"
          @click="inviteUser(result.pk)"
        >
          <UserAvatar :src="result.avatar_url || ''" :name="userFullName(result)" fallback="icon" />
          {{ result.first_name || '' }}
          {{ result.last_name || '' }}
          ({{ result.username || result.email || '' }})
        </button>
      </div>
      <p
        v-if="searchQuery.length >= 3 && searchResults.length === 0"
        class="text-sm text-gray-500 dark:text-gray-400 mt-1"
      >
        No users found.
      </p>
    </div>

    <!-- Pending Invitations -->
    <div v-if="invites.length > 0" class="mb-6">
      <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Pending Invitations</h4>
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th class="pb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Name</th>
            <th class="pb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Email</th>
            <th class="pb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Status</th>
            <th class="pb-2" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="invite in invites" :key="invite.pk" class="border-b border-gray-100 dark:border-gray-700">
            <td class="py-2 text-gray-900 dark:text-white">
              <UserBadge v-if="invite.invitee" :user="invite.invitee" fallback="icon" />
            </td>
            <td class="py-2 text-gray-700 dark:text-gray-300">
              {{ invite.invitee_email || '' }}
            </td>
            <td class="py-2">
              <span
                class="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"
              >
                Pending
              </span>
            </td>
            <td class="py-2 text-right">
              <button
                class="cursor-pointer inline-flex items-center gap-1 rounded p-1.5 text-sm text-gray-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                @click="cancelInvite(invite)"
              >
                <XMarkIcon class="h-4 w-4" />
                Cancel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Invite by Email Modal -->
    <AppModal :open="inviteEmailModalOpen" title="Invite by Email" @close="inviteEmailModalOpen = false">
      <div class="mb-4">
        <label for="invite-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >Email Address</label
        >
        <input
          id="invite-email"
          v-model="inviteEmail"
          type="email"
          class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          @keyup.enter="sendEmailInvite"
        />
        <p v-if="inviteEmailError" class="mt-1 text-sm text-red-600">
          {{ inviteEmailError }}
        </p>
      </div>
      <template #footer>
        <button
          class="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
          @click="inviteEmailModalOpen = false"
        >
          Cancel
        </button>
        <button
          class="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          @click="sendEmailInvite"
        >
          Send Invite
        </button>
      </template>
    </AppModal>

    <ConfirmModal ref="confirmRef" />
  </div>
</template>

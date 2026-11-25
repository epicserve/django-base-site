<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ArrowPathIcon, UserMinusIcon, EnvelopeIcon, XMarkIcon } from '@heroicons/vue/24/outline';
import type { components } from '../api/schema';
import { api, getAllResults, parseErrors, unwrap } from '../utils/api';
import { showToast } from '../composables/useToast';
import { userFullName } from '../utils/format';
import AppModal from '../components/AppModal.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import UserBadge from '../components/UserBadge.vue';

type Member = components['schemas']['MemberOut'];
type Invite = components['schemas']['InviteOut'];
type Role = components['schemas']['OrgRole'];

// A role the API adds needs a label here, or vue-tsc fails.
const ROLE_LABELS: Record<Role, string> = { owner: 'Owner', member: 'Member' };

const props = defineProps<{ orgName: string; currentUserId: number }>();

const members = ref<Member[]>([]);
const invites = ref<Invite[]>([]);
const inviteEmailModalOpen = ref(false);
const inviteEmail = ref('');
const inviteEmailError = ref('');
const confirmRef = ref<InstanceType<typeof ConfirmModal> | null>(null);

async function loadData() {
  try {
    // Both lists are paginated; load every page so nothing past the first is silently dropped.
    [members.value, invites.value] = await Promise.all([
      getAllResults((page) => unwrap(api.GET('/api/organization-members/', { params: { query: { page } } }))),
      getAllResults((page) => unwrap(api.GET('/api/organization-invites/', { params: { query: { page } } }))),
    ]);
  } catch {
    showToast('Failed to load data.', 'error');
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
    await unwrap(api.POST('/api/organization-invites/', { body: { invitee_email: email } }));
    inviteEmailModalOpen.value = false;
    showToast('Invitation sent.');
    await loadData();
  } catch (err) {
    const errors = parseErrors(err);
    inviteEmailError.value = Object.values(errors).flat().join(' ');
  }
}

async function changeRole(member: Member) {
  // Switches between the template's two roles. A project that adds roles would offer a choice here instead.
  const newRole: Role = member.role === 'owner' ? 'member' : 'owner';
  const confirmed = await confirmRef.value?.confirm(
    `Change ${userFullName(member.user)}'s role from ${member.role} to ${newRole}?`,
    'Change Role',
  );
  if (!confirmed) return;
  try {
    await unwrap(
      api.PATCH('/api/organization-members/{member_id}/', {
        params: { path: { member_id: member.pk } },
        body: { role: newRole },
      }),
    );
    showToast('Role updated.');
    await loadData();
  } catch {
    showToast('Failed to change role.', 'error');
  }
}

async function removeMember(member: Member) {
  const confirmed = await confirmRef.value?.confirm(
    `Remove ${userFullName(member.user)} from ${props.orgName}?`,
    'Remove Member',
  );
  if (!confirmed) return;
  try {
    await unwrap(api.DELETE('/api/organization-members/{member_id}/', { params: { path: { member_id: member.pk } } }));
    showToast('Member removed.');
    await loadData();
  } catch {
    showToast('Failed to remove member.', 'error');
  }
}

async function cancelInvite(invite: Invite) {
  const confirmed = await confirmRef.value?.confirm('Cancel this invitation?', 'Cancel Invite');
  if (!confirmed) return;
  try {
    await unwrap(api.DELETE('/api/organization-invites/{invite_id}/', { params: { path: { invite_id: invite.pk } } }));
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
              <UserBadge :user="member.user" fallback="icon" />
            </td>
            <td class="py-2 text-gray-700 dark:text-gray-300">
              {{ member.user.email || member.user.username }}
            </td>
            <td class="py-2">
              <span
                :class="[
                  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                  member.role === 'owner'
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
                ]"
              >
                {{ ROLE_LABELS[member.role] }}
              </span>
            </td>
            <td class="py-2 text-right">
              <button
                :disabled="member.user.id === currentUserId"
                class="cursor-pointer inline-flex items-center gap-1 rounded p-1.5 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed dark:hover:bg-gray-700 dark:hover:text-gray-300"
                title="Change Role"
                @click="changeRole(member)"
              >
                <ArrowPathIcon class="h-4 w-4" />
                Change Role
              </button>
              <button
                :disabled="member.user.id === currentUserId"
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
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">They'll get an email with a link to join.</p>
      <button
        class="cursor-pointer inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        @click="openInviteByEmailModal"
      >
        <EnvelopeIcon class="h-4 w-4" />
        Invite by Email
      </button>
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
                v-if="invite.is_expired"
                class="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900/30 dark:text-red-300"
              >
                Expired
              </span>
              <span
                v-else
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
          :aria-invalid="inviteEmailError ? 'true' : undefined"
          :aria-describedby="inviteEmailError ? 'invite-email-error' : undefined"
          class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          @keyup.enter="sendEmailInvite"
        />
        <p v-if="inviteEmailError" id="invite-email-error" class="mt-1 text-sm text-red-600">
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

import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { ApiError, api } from '@/utils/api';
import { initAppStore } from '@/stores/app';
import AcceptInviteView from './AcceptInviteView.vue';

vi.mock('@/utils/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/utils/api')>();
  return { ...actual, api: { GET: vi.fn(), POST: vi.fn() } };
});

const invite = {
  organization_name: 'Dunder Mifflin',
  sender_name: 'Michael Scott',
  invitee_email: 'ryan.howard@dundermifflin.example',
  is_expired: false,
  is_already_member: false,
};

function rejectWith(status: number, data: unknown) {
  vi.mocked(api.POST).mockRejectedValue(new ApiError(new Response(null, { status }), data));
}

describe('AcceptInviteView', () => {
  let wrapper: VueWrapper | undefined;

  beforeEach(() => {
    vi.mocked(api.GET).mockResolvedValue({ data: invite, response: new Response() });
    initAppStore().setUser({
      id: 1,
      email: 'ron.swanson@pawnee.example',
      username: 'ron.swanson',
      first_name: 'Ron',
      last_name: 'Swanson',
      avatar_url: null,
      timezone: 'America/Chicago',
      timezone_display: 'Central Time',
      is_staff: false,
      is_superuser: false,
      is_hijacked: false,
      impersonation_banner_hidden: false,
      organizations: [],
    });
  });

  afterEach(() => {
    wrapper?.unmount();
    vi.resetAllMocks();
  });

  async function openInvite() {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div />' } },
        { path: '/accounts/login/', name: 'login', component: { template: '<div />' } },
        { path: '/accounts/signup/', name: 'signup', component: { template: '<div />' } },
        { path: '/organizations/invite/:key/accept/', name: 'accept-invite', component: AcceptInviteView },
      ],
    });
    await router.push('/organizations/invite/abc123/accept/');
    wrapper = mount(AcceptInviteView, { global: { plugins: [router] } });
    await flushPromises();
    return wrapper;
  }

  async function click(name: string) {
    const page = await openInvite();
    const button = page.findAll('button').find((b) => b.text() === name);
    if (!button) throw new Error(`No "${name}" button`);
    await button.trigger('click');
    await flushPromises();
    return page;
  }

  for (const action of ['Accept Invitation', 'Decline']) {
    test(`shows the server's reason when "${action}" is refused`, async () => {
      rejectWith(403, { detail: 'This invitation was sent to a different email address.' });

      const page = await click(action);

      expect(page.find('h1').text()).toBe('Invitation Unavailable');
      expect(page.text()).toContain('This invitation was sent to a different email address.');
      expect(page.text()).not.toContain('HTTP 403');
    });
  }

  for (const [action, fallback] of [
    ['Accept Invitation', 'Failed to accept the invitation.'],
    ['Decline', 'Failed to decline the invitation.'],
  ]) {
    test(`falls back to its own message when "${action}" fails without a reason`, async () => {
      rejectWith(500, null);

      const page = await click(action);

      expect(page.text()).toContain(fallback);
      expect(page.text()).not.toContain('HTTP 500');
    });
  }
});

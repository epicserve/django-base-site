import { afterEach, describe, expect, test, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import AccountPasswordChangeView from './AccountPasswordChangeView.vue';
import { authApi } from '../api';

vi.mock('../api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api')>();
  return { ...actual, authApi: { ...actual.authApi, changePassword: vi.fn() } };
});

function mountView() {
  return mount(AccountPasswordChangeView, {
    global: { stubs: { AccountLayout: { template: '<div><slot /></div>' } } },
  });
}

function input(wrapper: ReturnType<typeof mountView>, label: string) {
  const forLabel = wrapper.findAll('label').find((el) => el.text() === label);
  if (!forLabel) throw new Error(`No field is labeled ${label}`);
  return wrapper.get(`#${forLabel.attributes('for')}`);
}

async function submit(wrapper: ReturnType<typeof mountView>, newPassword: string, newPasswordAgain: string) {
  await input(wrapper, 'Current Password').setValue('dev-password');
  await input(wrapper, 'New Password').setValue(newPassword);
  await input(wrapper, 'New Password (Again)').setValue(newPasswordAgain);
  await wrapper.get('form').trigger('submit');
  await flushPromises();
}

describe('AccountPasswordChangeView', () => {
  afterEach(() => {
    vi.mocked(authApi.changePassword).mockReset();
  });

  test("doesn't change the password when the new passwords don't match", async () => {
    // It used to send only the first new password, so a typo in it became the password.
    const wrapper = mountView();

    await submit(wrapper, 'first-Secret-123', 'other-Secret-456');

    expect(authApi.changePassword).not.toHaveBeenCalled();
    const again = input(wrapper, 'New Password (Again)');
    expect(again.attributes('aria-invalid')).toBe('true');
    expect(wrapper.get(`#${again.attributes('aria-describedby')}`).text()).toBe("The passwords don't match.");
    expect(input(wrapper, 'New Password').attributes('aria-invalid')).toBeUndefined();
  });

  test('changes the password when the new passwords match', async () => {
    vi.mocked(authApi.changePassword).mockResolvedValue(undefined);
    const wrapper = mountView();

    await submit(wrapper, 'first-Secret-123', 'first-Secret-123');

    expect(authApi.changePassword).toHaveBeenCalledWith({
      current_password: 'dev-password',
      new_password: 'first-Secret-123',
    });
    expect(input(wrapper, 'New Password (Again)').attributes('aria-invalid')).toBeUndefined();
  });
});

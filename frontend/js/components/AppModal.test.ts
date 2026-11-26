import { afterEach, describe, expect, test } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { nextTick } from 'vue';
import AppModal from './AppModal.vue';

describe('AppModal', () => {
  let wrapper: VueWrapper | undefined;

  afterEach(() => {
    wrapper?.unmount();
    document.body.innerHTML = '';
  });

  async function open(props: { title?: string } = {}) {
    wrapper = mount(AppModal, {
      props: { open: true, title: 'Edit Team', ...props },
      slots: { default: '<p>Body</p>' },
      attachTo: document.body,
    });
    await nextTick();
    return wrapper;
  }

  function closeButton(): HTMLButtonElement {
    const button = document.body.querySelector<HTMLButtonElement>('button[aria-label]');
    if (!button) throw new Error('The modal has no button with a name');
    return button;
  }

  test('names its close button, which holds only an icon', async () => {
    await open();

    expect(closeButton().getAttribute('aria-label')).toBe('Close');
    expect(closeButton().textContent?.trim()).toBe('');
  });

  test('is a dialog named by its title', async () => {
    await open();

    const dialog = document.body.querySelector('[role="dialog"]');
    const titleId = dialog?.getAttribute('aria-labelledby');
    expect(titleId).toBeTruthy();
    expect(document.getElementById(titleId ?? '')?.textContent?.trim()).toBe('Edit Team');
    expect(dialog?.textContent).toContain('Body');
  });

  test('emits close when the close button is clicked', async () => {
    const modal = await open();

    closeButton().click();
    await nextTick();

    expect(modal.emitted('close')).toHaveLength(1);
  });
});

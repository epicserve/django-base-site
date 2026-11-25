import { describe, expect, test } from 'vitest';
import { mount } from '@vue/test-utils';
import FormField from './FormField.vue';

describe('FormField', () => {
  test('its label names its input', () => {
    const wrapper = mount(FormField, { props: { label: 'Email Address' } });

    const input = wrapper.get('input');
    expect(wrapper.get('label').attributes('for')).toBe(input.attributes('id'));
    expect(wrapper.get('label').text()).toBe('Email Address');
  });

  test('without errors, the input is valid and has no description', () => {
    const wrapper = mount(FormField, { props: { label: 'Name' } });

    const input = wrapper.get('input');
    expect(input.attributes('aria-invalid')).toBeUndefined();
    expect(input.attributes('aria-describedby')).toBeUndefined();
  });

  test('its errors describe its input, so a screen reader reads them with it', () => {
    const wrapper = mount(FormField, { props: { label: 'Name', errors: ['Name is required.', 'Too short.'] } });

    const input = wrapper.get('input');
    expect(input.attributes('aria-invalid')).toBe('true');
    const description = wrapper.get(`#${input.attributes('aria-describedby')}`);
    expect(description.findAll('p').map((error) => error.text())).toEqual(['Name is required.', 'Too short.']);
  });

  test('passes attributes that are not props to the input, not its wrapper', () => {
    // The two-factor code field's `inputmode` used to land on the wrapper <div>, so phones showed the full keyboard.
    const wrapper = mount(FormField, { props: { label: 'Code' }, attrs: { inputmode: 'numeric', maxlength: '6' } });

    expect(wrapper.get('input').attributes('inputmode')).toBe('numeric');
    expect(wrapper.get('input').attributes('maxlength')).toBe('6');
    expect(wrapper.element.getAttribute('inputmode')).toBeNull();
  });

  test("attributes passed in can't replace its id or error wiring", () => {
    const wrapper = mount(FormField, {
      props: { label: 'Name', errors: ['Name is required.'] },
      attrs: { id: 'other', 'aria-describedby': 'elsewhere' },
    });

    const input = wrapper.get('input');
    expect(wrapper.get('label').attributes('for')).toBe(input.attributes('id'));
    expect(input.attributes('id')).not.toBe('other');
    expect(input.attributes('aria-describedby')).not.toBe('elsewhere');
  });

  test('emits what is typed', async () => {
    const wrapper = mount(FormField, { props: { label: 'Name', modelValue: '' } });

    await wrapper.get('input').setValue('Sales');

    expect(wrapper.emitted('update:modelValue')).toEqual([['Sales']]);
  });
});

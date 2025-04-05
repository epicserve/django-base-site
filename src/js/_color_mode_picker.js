/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2022 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
  const storedTheme = localStorage.getItem('theme'),

    getPreferredTheme = () => {
      if (storedTheme) {
        return storedTheme;
      }

      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    // eslint-disable-next-line func-names
    setTheme = function (theme) {
      if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
      } else {
        document.documentElement.setAttribute('data-bs-theme', theme);
      }
    };

  setTheme(getPreferredTheme());

  // eslint-disable-next-line one-var
  const showActiveTheme = (theme) => {
    const activeThemeIcon = document.querySelector('.theme-icon-active use'),
      btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`);

    if (!btnToActive) return;

    // eslint-disable-next-line one-var
    const svgOfActiveBtn = btnToActive.querySelector('svg use').getAttribute('href');

    document.querySelectorAll('[data-bs-theme-value]').forEach((element) => {
      element.classList.remove('active');
    });

    btnToActive.classList.add('active');
    activeThemeIcon.setAttribute('href', svgOfActiveBtn);
  };

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (storedTheme !== 'light' || storedTheme !== 'dark') {
      setTheme(getPreferredTheme());
    }
  });

  window.addEventListener('DOMContentLoaded', () => {
    showActiveTheme(getPreferredTheme());

    document.querySelectorAll('[data-bs-theme-value]')
      .forEach((toggle) => {
        toggle.addEventListener('click', () => {
          const theme = toggle.getAttribute('data-bs-theme-value');
          localStorage.setItem('theme', theme);
          setTheme(theme);
          showActiveTheme(theme);
        });
      });
  });
})();

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
      const html = document.documentElement;
      
      if (theme === 'auto') {
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
          html.classList.add('dark');
        } else {
          html.classList.remove('dark');
        }
      } else if (theme === 'dark') {
        html.classList.add('dark');
      } else {
        html.classList.remove('dark');
      }
    };

  setTheme(getPreferredTheme());

  // eslint-disable-next-line one-var
  const showActiveTheme = (theme) => {
    const activeThemeIcon = document.querySelector('.theme-icon-active use'),
      btnToActive = document.querySelector(`[data-theme-value="${theme}"]`);

    if (!btnToActive) return;

    // eslint-disable-next-line one-var
    const svgOfActiveBtn = btnToActive.querySelector('svg use').getAttribute('href');

    document.querySelectorAll('[data-theme-value]').forEach((element) => {
      element.classList.remove('bg-gray-100', 'dark:bg-gray-700');
    });

    btnToActive.classList.add('bg-gray-100', 'dark:bg-gray-700');
    activeThemeIcon.setAttribute('href', svgOfActiveBtn);
  };

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (storedTheme !== 'light' && storedTheme !== 'dark') {
      setTheme(getPreferredTheme());
    }
  });

  // Make setTheme available globally for Alpine.js
  window.setTheme = (theme) => {
    localStorage.setItem('theme', theme);
    setTheme(theme);
    showActiveTheme(theme);
  };

  window.addEventListener('DOMContentLoaded', () => {
    showActiveTheme(getPreferredTheme());

    document.querySelectorAll('[data-theme-value]')
      .forEach((toggle) => {
        toggle.addEventListener('click', () => {
          const theme = toggle.getAttribute('data-theme-value');
          window.setTheme(theme);
        });
      });
  });
})();

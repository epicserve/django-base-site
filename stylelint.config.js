module.exports = {
  extends: [
    // Use the Standard config as the base
    // https://github.com/stylelint/stylelint-config-standard
    'stylelint-config-standard',
    // Enforce a standard order for CSS properties
    // https://github.com/stormwarning/stylelint-config-recess-order
    'stylelint-config-recess-order',
  ],
  plugins: [
    // Bring in some extra rules for SCSS
    'stylelint-scss',
  ],
  rules: {
    'import-notation': 'string'
  },
};

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
  // Rule lists:
  // - https://stylelint.io/user-guide/rules/
  // - https://github.com/kristerkari/stylelint-scss#list-of-rules
  rules: {
    // Allow newlines inside class attribute values
    'string-no-newline': null,
    // Limit the number of universal selectors in a selector,
    // to avoid very slow selectors
    'selector-max-universal': 1,
    // ===
    // SCSS
    // ===
    indentation: 2,
    'declaration-block-semicolon-newline-after': 'always',
    'declaration-colon-space-after': 'always',
    'declaration-colon-space-before': 'never',
    'declaration-block-trailing-semicolon': 'always',
    'selector-id-pattern': '^[a-z-_]+$',
    'selector-class-pattern': '^[a-z-_]+$',
    'scss/dollar-variable-colon-space-after': 'always',
    'scss/dollar-variable-colon-space-before': 'never',
    'scss/dollar-variable-no-missing-interpolation': true,
    'scss/dollar-variable-pattern': /^[a-z-]+$/,
    'scss/double-slash-comment-whitespace-inside': 'always',
    'scss/operator-no-newline-before': true,
    'scss/operator-no-unspaced': true,
    'scss/selector-no-redundant-nesting-selector': true,
    // Allow SCSS and CSS module keywords beginning with `@`
    'at-rule-no-unknown': null,
    'scss/at-rule-no-unknown': true,
    'block-opening-brace-newline-after': 'always',
    'block-closing-brace-newline-before': 'always',
    'block-closing-brace-newline-after': 'always',
    'block-opening-brace-space-before': 'always',
    'block-closing-brace-empty-line-before': 'never',
    'max-empty-lines': 1,
  },
};

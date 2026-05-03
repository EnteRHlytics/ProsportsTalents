/* eslint-env node */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  settings: {
    react: { version: 'detect' },
  },
  plugins: ['react', 'react-hooks'],
  rules: {
    // React 18 + new JSX transform: no need to import React in scope
    'react/jsx-uses-react': 'off',
    'react/react-in-jsx-scope': 'off',
    // Avoid noisy prop-types complaints in a JS (non-TS) codebase that does not use them
    'react/prop-types': 'off',
    // Treat unused vars as warnings, allow leading underscore opt-out
    'no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
      },
    ],
    // Common false-positive: unescaped quotes in JSX text are fine for our content
    'react/no-unescaped-entities': 'off',
  },
  overrides: [
    {
      files: ['tests/**/*.{js,jsx}', '**/*.test.{js,jsx}'],
      env: { node: true, jest: true },
      globals: {
        vi: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeAll: 'readonly',
        beforeEach: 'readonly',
        afterAll: 'readonly',
        afterEach: 'readonly',
        fetch: 'readonly',
      },
      rules: {
        'no-unused-vars': 'off',
      },
    },
  ],
  ignorePatterns: [
    'dist',
    'build',
    'node_modules',
    'coverage',
    '*.config.js',
    '*.config.cjs',
  ],
};

// Commitlint configuration — single source of truth for both
// the pre-commit `commit-msg` hook (local) and the CI Commit Message
// Validation workflow (PR gate). Conventional Commits, with our
// project's `type-enum` extended for catalog/dep work.
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation changes
        'style',    // Code style changes (formatting, missing semi-colons, etc)
        'refactor', // Code refactoring
        'perf',     // Performance improvements
        'test',     // Adding or updating tests
        'build',    // Build system changes
        'ci',       // CI/CD changes
        'chore',    // Other changes that don't modify src or test files
        'revert',   // Revert a previous commit
        'deps',     // Dependency updates
      ],
    ],
    'subject-case': [0],         // Allow any case for subject
    'body-max-line-length': [0], // Disable body line length check
  },
};

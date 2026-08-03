# CodeQL Security Scanning Configuration

This directory holds the CodeQL configuration that GitHub's code-scanning
workflow consumes. It does **not** contain custom queries — those live
in the sibling repo `cable-modem-monitor-ql/` (see § Custom Queries
below).

## What is CodeQL?

**GitHub's code analysis engine that finds security vulnerabilities
automatically.**

```text
Your Code → CodeQL Database → Queries → Security Alerts
```

1. **Build a database**: CodeQL parses your code into a queryable
   database (like SQL for code).
2. **Run queries**: Security queries ask things like "Is user input
   flowing into a SQL query without sanitization?"
3. **Report findings**: Matches appear as alerts in GitHub's Security
   tab.

## How it differs from Ruff / mypy

| Tool | Checks | How |
| --- | --- | --- |
| **Ruff** | Style, syntax, simple bugs | Pattern matching on single files |
| **mypy** | Type correctness | Type inference across files |
| **CodeQL** | Security vulnerabilities | Data flow analysis across the whole codebase |

Ruff catches `except:` (too broad). CodeQL traces user input flowing
through 5 functions into an `eval()` call — a real vulnerability that
a linter cannot detect.

## Why we use it

The integration handles network requests to devices, user
credentials, HTML parsing from untrusted sources, and file
operations. CodeQL catches injection, credential-in-log, missing
timeout, unsafe SSL, and path traversal classes of issues that
linters do not see.

The trade-off: CodeQL has false positives. `codeql-config.yml`
contains exclusions for patterns that are intentional in our context
(e.g., `verify=False` for self-signed cable modem certs).

## Files in this directory

```text
.github/codeql/
├── README.md          # This file
└── codeql-config.yml  # CodeQL configuration (paths-ignore, query filters)
```

That's all. The `queries/` subdirectory referenced in earlier
documentation never existed here — custom queries are developed and
tested in the sibling `cable-modem-monitor-ql/` repo.

## What CI actually runs

`.github/workflows/codeql.yml` invokes the standard query packs
only:

```yaml
queries: security-extended,security-and-quality
config-file: .github/codeql/codeql-config.yml
```

That gives us the OWASP / CWE coverage GitHub maintains (~100+
queries). **No custom queries run in CI** — they were removed from
the workflow due to CodeQL Action compatibility issues with our
custom-pack format. The custom query in the sibling repo is
exercised by the local pre-commit hook only.

`codeql-config.yml` configures behavior:

- **paths-ignore**: excludes tools, scripts, docs, and test fixtures
  from scanning
- **query-filters**: suppresses false positives for intentional
  patterns (SSL verify-disabled for self-signed certs, clear-text
  diagnostic logging, etc.)

## Custom queries (sibling repo)

Project-specific queries live in `cable-modem-monitor-ql/queries/`.
Currently:

- `no_timeout.ql` — flags HTTP requests without an explicit timeout

These run via the `codeql-test` pre-commit hook
(`scripts/dev/test-codeql.sh`), which uses the project-local CodeQL
CLI to exercise the queries against the test cases in
`cable-modem-monitor-ql/tests/`. They do **not** run in GitHub's
code-scanning workflow.

To add a query:

1. Develop in `cable-modem-monitor-ql/queries/`.
2. Add a test case in `cable-modem-monitor-ql/tests/`.
3. Run `bash scripts/dev/test-codeql.sh` locally.
4. Commit to `cable-modem-monitor-ql/`.

Promoting a custom query into the GitHub-hosted CI scan would
require resolving the CodeQL Action compatibility issue that caused
custom queries to be removed in the first place.

## Working with results

### View scan results

1. Repository → Security tab → Code scanning alerts.
2. Filter by severity, category, or query.

### Suppress a false positive

In code (preferred):

```python
# Justification comment explaining why this is safe
potentially_flagged_code()  # nosec B501
```

In the GitHub UI: open the alert, dismiss with reason.

For a project-wide pattern: add to `codeql-config.yml` `query-filters`
with rationale.

### Test locally

Requires the CodeQL CLI installed locally — see
[`docs/reference/CODEQL_TESTING_GUIDE.md`](../../docs/reference/CODEQL_TESTING_GUIDE.md)
for setup. Then:

```bash
bash scripts/dev/test-codeql.sh
```

## Status

- ✅ CI runs standard CodeQL packs (`security-extended`,
  `security-and-quality`) on push, PR, and a weekly schedule.
- ✅ 1 custom query in the sibling repo, exercised by the local
  pre-commit hook.
- ⚠️ Custom queries are **not** wired into CI — pending resolution of
  the CodeQL Action compatibility issue noted in the workflow.

Last updated: 2026-04-24

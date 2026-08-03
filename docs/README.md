# Project Documentation

Guides and references that span the full project. For package-specific
specs, see the indexes in each package's `docs/` directory.

## Users

| Document | Covers |
|----------|--------|
| [../INSTALL.md](../INSTALL.md) | Install, configure, migrate from the cable_modem_monitor fork, build the zip |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Connection problems, missing sensors, duplicate entities |
| [EXAMPLES.md](EXAMPLES.md) | Dashboard and automation examples |

## Contributors

| Document | Covers |
|----------|--------|
| [CODE_REVIEW.md](CODE_REVIEW.md) | Coding standards, test patterns, naming |
| [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md) | Localization process |
| [ATTRIBUTION.md](ATTRIBUTION.md) | Upstream credit and third-party acknowledgments |
| [setup/GETTING_STARTED.md](setup/GETTING_STARTED.md) | Environment setup and daily workflow |

## Reference

| Document | Covers |
|----------|--------|
| [reference/RELEASING.md](reference/RELEASING.md) | Release process |
| [reference/LINTING.md](reference/LINTING.md) | Linter configuration and rules |
| [reference/CODEQL_TESTING_GUIDE.md](reference/CODEQL_TESTING_GUIDE.md) | CodeQL test patterns |
| [`.github/codeql/README.md`](../.github/codeql/README.md) | CodeQL configuration and suppressed-rule rationales |

## Package Specs (separate indexes)

| Index | Scope |
|-------|-------|
| [Core specs](../packages/cable_modem_monitor_core/docs/README.md) | Architecture, auth, parsing, orchestration |
| [Catalog docs](../packages/cable_modem_monitor_catalog/docs/README.md) | Device data, mock server |
| [Catalog Tools docs](../packages/cable_modem_monitor_catalog_tools/docs/README.md) | HAR analysis, golden-file generation |
| [HA specs](../custom_components/bgw320/docs/README.md) | Config flow, entities, adapter wiring |

## A note on package names

The engine packages are still named `cable_modem_monitor_core`,
`cable_modem_monitor_catalog`, and `cable_modem_monitor_catalog_tools`, and
import under the `solentlabs` namespace. They are kept at their upstream names
deliberately: they are vendored into the release artifact rather than resolved
from PyPI, the names are invisible to users, and renaming them would create a
large diff against upstream for no functional gain — making future merges of
upstream engine fixes harder to apply.

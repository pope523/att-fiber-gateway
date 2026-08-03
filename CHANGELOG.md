# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project was split out of
[solentlabs/cable_modem_monitor](https://github.com/solentlabs/cable_modem_monitor).
Changelog entries for the shared engine prior to 1.0.0 live in that project's
history.

## [Unreleased]

## [1.0.0] - 2026-08-03

First release as a standalone integration for the AT&T Nokia BGW320-505
XGS-PON fiber gateway.

### Added

- **Fiber optical sensors.** Optical Rx power, Tx power, and SFP module
  temperature as graphable sensors. The current values live in
  `<h1>… Currently N</h1>` headers on `fiberstat.ha` — the page's tables hold
  only thresholds — so a post-processor extracts them and scales power by 1/10
  to dBm.
- **PON and WAN sensors.** Optical WAN operational status, link state,
  wavelength, raw GPON state, connection/network type, negotiated link speed,
  public IPv4/IPv6, and receive/transmit byte, packet, error, and drop counters.
- **Device sensors.** Firmware version, hardware version, uptime, and derived
  last boot time.
- **Restart button.** New `form_md5_nonce` auth strategy: GET the login page for
  a server nonce, POST `md5(access_code + nonce)`, then POST the reboot with a
  freshly fetched per-request nonce. Needs the 12-character Device Access Code;
  monitoring stays credential-free. Verified live against firmware 6.34.7.
- **Self-contained HACS artifact.** `scripts/dev/build_hacs_zip.py` vendors the
  engine packages into `bgw320.zip`, so installation pulls nothing from PyPI
  under the `solentlabs` name.

### Changed

- **Domain is `bgw320`**, display name "AT&T BGW320 Gateway". Entities are
  `sensor.bgw320_*`; the Home Assistant device is named `BGW320`.
- **`docsis_status` is now `pon_status`** (and `DocsisStatus` is `PonStatus`)
  throughout core, catalog, the adapter, and fixtures.
- **Channel-less devices report ONLINE.** `derive_connection_status` treats an
  operational optical link as online instead of NO_SIGNAL, which assumed a
  cable modem that failed to lock channels.
- **`docsis_version` is optional** in device metadata, so non-DOCSIS hardware
  validates.
- The catalog contains a single device, the BGW320-505.

### Removed

- **DS/US channel-count sensors.** The parser coordinator still emits both
  counts, but XGS-PON has no DOCSIS channels, so they were permanently 0.
- **Channel-bond change notifications** and their `Store`. Without channel
  bonding they had nothing to report, and the check ran on every poll.

### Fixed

- **Diagnostics dropped engine logs.** Log filtering matched a substring of the
  old domain, which incidentally also matched the engine's logger name.
  Renaming the domain would have silently excluded every engine record, so the
  filter is now an explicit predicate over both logger prefixes.
- **`trial_parse` mis-handled channel-less configs.** It detected parser
  sections by substring-matching the raw YAML text, so a config whose *comments*
  mention "downstream" was treated as declaring one and failed with "extracted
  0 channels". It also required at least one channel to pass, so a correct
  system_info-only parser never could. Section detection is now structural and
  system_info counts as extraction.
- **The self-containment check in the build script was vacuous** after the
  rename: it filtered `sys.path` on a directory name that no longer matched, so
  the editable install could satisfy the import the check was meant to isolate.

[Unreleased]: https://github.com/pope523/att-fiber-gateway/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/pope523/att-fiber-gateway/releases/tag/v1.0.0

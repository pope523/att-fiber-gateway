# Installing AT&T BGW320 Gateway

## Why the release zip is self-contained

The integration's collection/parsing engine lives in two local packages,
`solentlabs.cable_modem_monitor_core` and `solentlabs.cable_modem_monitor_catalog`.
They carry BGW320-specific changes (fiber status derivation, the
`form_md5_nonce` auth strategy, per-request nonce injection) and are **not**
published to PyPI under those names.

So the HACS artifact bundles them. `scripts/dev/build_hacs_zip.py` copies both
packages into `_vendor/solentlabs/` inside the zip and injects a small
`sys.path` bootstrap that makes them importable at runtime. Home Assistant
installs only ordinary third-party dependencies (beautifulsoup4, pydantic,
requests, pyyaml, defusedxml, cryptography); nothing is fetched from PyPI under
the `solentlabs` name.

The bootstrap *appends* to `sys.path`, so a real pip/editable install still
wins if one is present. That makes it a no-op in a development checkout.

## Install on Home Assistant

### Option A — HACS custom repository (recommended)

1. HACS → three-dot menu → **Custom repositories**.
2. Add `https://github.com/pope523/att-fiber-gateway`, category **Integration**.
3. Install **AT&T BGW320 Gateway**.
4. Restart Home Assistant.
5. Settings → Devices & Services → **Add Integration** → "AT&T BGW320 Gateway".

### Option B — Manual

1. Download `bgw320.zip` from the
   [releases page](https://github.com/pope523/att-fiber-gateway/releases).
2. Unzip into `config/custom_components/bgw320/` on the Home Assistant host.
   The integration files must sit at that path directly — `manifest.json`
   should be at `config/custom_components/bgw320/manifest.json`.
3. Restart Home Assistant and add the integration.

## Configuring the BGW320-505

- **Host:** `192.168.0.254` (the AT&T default).
- **Monitoring** needs no credentials; the status pages are readable
  unauthenticated.
- **Restart button:** enter the 12-character **Device Access Code** from the
  gateway's label as the password. It is stored as the entry credential and
  used only for the restart action's server-nonce + MD5 login. Polling stays
  credential-free.

Leave the password blank if you only want monitoring. You can add it later via
**Configure** on the integration.

## Migrating from the cable_modem_monitor fork

This integration uses the domain `bgw320`, so it will not adopt entities from a
previous `cable_modem_monitor` install. Entity history does not carry over.

1. Settings → Devices & Services → **Cable Modem Monitor** → delete the entry.
2. Remove it from HACS (or delete `config/custom_components/bgw320/`).
3. Install this integration and add it fresh.
4. Update dashboards and automations from `sensor.cable_modem_*` to
   `sensor.bgw320_*`. Note `docsis_status` is now `pon_status`, and the DS/US
   channel-count sensors no longer exist.

## Building the zip yourself

```
python scripts/dev/build_hacs_zip.py
```

Writes `bgw320.zip` and verifies it in an isolated interpreter: the check strips
the editable engine sources from `sys.path`, imports only from `_vendor/`, and
loads the BGW320-505 catalog entry including its restart action. Pass
`--no-verify` to skip that check, or `--output PATH` to write elsewhere.

## Releasing

Tag a release so the `Release` workflow builds and attaches the zip. The tag
must match `version` in `custom_components/bgw320/manifest.json`:

```
git tag v1.0.0 && git push origin v1.0.0
```

HACS reads `hacs.json`, which points at the `bgw320.zip` release asset.

## Development setup

The project targets **Python 3.12** (`mypy.ini` and every CI job). Building the
venv on a newer interpreter will resolve a Home Assistant build whose
type-parameter-default syntax mypy rejects under `python_version = 3.12`.

```
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install -e packages/cable_modem_monitor_core \
                      -e packages/cable_modem_monitor_catalog \
                      -e packages/cable_modem_monitor_catalog_tools
```

Run the suites:

```
.venv/bin/python -m pytest tests/ -q                                    # HA adapter
(cd packages/cable_modem_monitor_core && ../../.venv/bin/python -m pytest tests/ -q)
(cd packages/cable_modem_monitor_catalog && ../../.venv/bin/python -m pytest tests/ -q --no-cov)
(cd packages/cable_modem_monitor_catalog_tools && ../../.venv/bin/python -m pytest tests/ -q --no-cov)
```

Lint and format:

```
.venv/bin/ruff check .
.venv/bin/black --check .
```

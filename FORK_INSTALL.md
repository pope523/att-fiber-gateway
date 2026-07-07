# Installing this fork (self-contained HACS build)

This fork adds monitoring + restart support for the **AT&T Nokia BGW320-505**
XGS-PON fiber gateway.

Upstream ships the Home Assistant integration as a HACS zip and pulls its
engines (`solentlabs-cable-modem-monitor-core` and `-catalog`) from PyPI. This
fork's engine changes are not published to PyPI, so the release zip is
**self-contained**: `scripts/dev/build_hacs_zip.py` bundles the two engine
packages under `_vendor/` and injects a small `sys.path` bootstrap that makes
them importable at runtime. Only ordinary third-party dependencies
(beautifulsoup4, pydantic, requests, pyyaml, defusedxml, cryptography) are
installed by Home Assistant; nothing is pulled from PyPI under the `solentlabs`
name.

## Build the zip

```
python scripts/dev/build_hacs_zip.py
```

This writes `cable_modem_monitor.zip` and verifies it imports in an isolated
interpreter (drop `--verify` with `--no-verify` to skip the check).

## Install on Home Assistant

**Option A — HACS custom repository (recommended)**

1. Tag a release on the fork so the `Release` workflow builds and attaches the
   zip:
   ```
   git tag v3.14.0-beta.12 && git push fork v3.14.0-beta.12
   ```
   (the tag must match the `version` in `custom_components/cable_modem_monitor/manifest.json`)
2. In HACS, open the three-dot menu, choose **Custom repositories**, and add the
   fork URL with category **Integration**.
3. Install **Cable Modem Monitor**, restart Home Assistant, then add it under
   **Settings -> Devices & Services**.

**Option B — Manual copy**

1. `python scripts/dev/build_hacs_zip.py`
2. Unzip into `config/custom_components/cable_modem_monitor/` on the HA host.
3. Restart Home Assistant and add the integration.

## Configuring the BGW320-505

- **Host:** `192.168.0.254` (default AT&T gateway address).
- **Monitoring** needs no credentials — the status pages are read-only.
- The **Restart** button needs your 12-character **Device Access Code** (printed
  on the gateway label). Enter it as the password on the connection form; it is
  stored as the entry credential and used only for the restart action's
  server-nonce + MD5 login. Monitoring itself stays credential-free.

# AT&T BGW320 Gateway

[![GitHub Release](https://img.shields.io/github/v/release/pope523/att-fiber-gateway?include_prereleases)](https://github.com/pope523/att-fiber-gateway/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Home Assistant integration for AT&T XGS-PON fiber gateways — the **Nokia
BGW320-505** and **CommScope BGW620-700**. Graphs the optical link, tracks
WAN health and throughput counters, and adds a restart button.

This is a fiber integration. It is not a DOCSIS cable modem integration — see
[Relationship to Cable Modem Monitor](#relationship-to-cable-modem-monitor).

## What you get

- **Fiber optics as first-class sensors.** Optical Rx power, Tx power, and SFP
  module temperature, read from the gateway's `fiberstat` page and graphable
  over time. Rx power is the number to watch: a slow decline usually means a
  dirty or bending fiber, and it degrades well before the link actually drops.
- **PON link state.** Optical WAN operational status, link state, wavelength,
  and the raw GPON state (`OPERATION (O5)` when healthy).
- **WAN status and throughput.** Connection type, network type, negotiated link
  speed, public IPv4/IPv6, and receive/transmit byte, packet, error, and drop
  counters.
- **Device info.** Firmware version, hardware version, uptime, and derived last
  boot time.
- **Health probes.** TCP, ping, and HTTP latency on a fast cadence (30s by
  default) independent of the full data poll (10 minutes by default).
- **Restart button.** Reboots the gateway using its nonce + MD5 login.
- **Local only.** No cloud, no telemetry. Everything is read from the gateway's
  own web interface on your LAN.

Monitoring needs **no credentials** — the BGW320's status pages are readable
without logging in. Only the restart button requires the Device Access Code.

## Requirements

- Home Assistant 2024.12.0 or newer
- An AT&T Nokia BGW320-505 or CommScope BGW620-700 reachable on your network
  (default `192.168.0.254`)
- HACS, for the recommended install path

The **BGW320-505** is verified on real hardware. The **BGW620-700** catalog
entry is newly added and still awaiting broader hardware confirmation (see
[CATALOG_AUDIT.md](https://github.com/pope523/att-fiber-gateway/blob/main/packages/cable_modem_monitor_catalog/CATALOG_AUDIT.md)).
The BGW320-500 is a similar Humax-built unit on the BGW320-505's firmware
family; it may work, but no fixtures exist for it and it is untested here.

## Install

**HACS custom repository (recommended)**

1. HACS → three-dot menu → **Custom repositories**.
2. Add `https://github.com/pope523/att-fiber-gateway` with category
   **Integration**.
3. Install **AT&T BGW320 Gateway**, then restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → "AT&T BGW320 Gateway".

**Manual**

Download `bgw320.zip` from a [release](https://github.com/pope523/att-fiber-gateway/releases)
and unzip it into `config/custom_components/bgw320/`, then restart Home
Assistant.

Full details, including building the zip yourself, are in
[INSTALL.md](https://github.com/pope523/att-fiber-gateway/blob/main/INSTALL.md).

## Setup

Pick your gateway's manufacturer and model (Nokia BGW320-505 or CommScope
BGW620-700), then enter:

- **Host:** `192.168.0.254` (the AT&T default).
- **Password:** optional. Leave blank for monitoring only. To enable the
  restart button, enter the **12-character Device Access Code** printed on the
  gateway's label.

The access code is stored in Home Assistant's encrypted credential storage and
is used only to authenticate the restart action. Polling never sends it.

## Entities

Entities are prefixed `bgw320_`, for example `sensor.bgw320_optical_rx_power`.

| Entity | Notes |
|---|---|
| `sensor.bgw320_status` | Rolled-up status from connection, health, and PON state |
| `sensor.bgw320_pon_status` | Optical WAN operational status (`Operational` when up) |
| `sensor.bgw320_pon_link_status` | Raw GPON state, e.g. `OPERATION (O5)` |
| `sensor.bgw320_optical_rx_power` | Receive power, dBm |
| `sensor.bgw320_optical_tx_power` | Transmit power, dBm |
| `sensor.bgw320_optical_temperature` | SFP module temperature |
| `sensor.bgw320_optical_status` | Optical link state |
| `sensor.bgw320_optical_wavelength` | Wavelength, e.g. `1270 nm` |
| `sensor.bgw320_wan_link_speed_mbps` | Negotiated WAN speed |
| `sensor.bgw320_wan_connection_type` | e.g. `FIBER` |
| `sensor.bgw320_wan_network_type` | e.g. `Lightspeed` |
| `sensor.bgw320_wan_ipv4` / `_wan_ipv6` | Public WAN addresses |
| `sensor.bgw320_wan_rx_bytes` / `_wan_tx_bytes` | Throughput counters |
| `sensor.bgw320_wan_rx_packets` / `_wan_tx_packets` | Packet counters |
| `sensor.bgw320_wan_rx_errors` / `_wan_tx_errors` | Error counters |
| `sensor.bgw320_wan_rx_drops` / `_wan_tx_drops` | Drop counters |
| `sensor.bgw320_software_version` | Firmware, e.g. `6.34.7` |
| `sensor.bgw320_hardware_version` | Hardware revision |
| `sensor.bgw320_system_uptime` | Uptime since last reboot |
| `sensor.bgw320_last_boot_time` | Timestamp derived from uptime |
| `sensor.bgw320_tcp_latency` | TCP connect latency |
| `sensor.bgw320_ping_latency` | ICMP latency |
| `sensor.bgw320_http_latency` | HTTP HEAD latency |
| `button.bgw320_restart_modem` | Reboot (needs the access code) |
| `button.bgw320_update_modem_data` | Force an immediate poll |
| `button.bgw320_reset_entities` | Re-run capability detection |

Optical temperature is reported in Celsius and displayed in your Home Assistant
unit system, so a US install shows Fahrenheit.

## Relationship to Cable Modem Monitor

This integration is derived from
[solentlabs/cable_modem_monitor](https://github.com/solentlabs/cable_modem_monitor),
a DOCSIS cable modem integration by Ken Schulz, and reuses its collection,
parsing, and orchestration engine under the MIT license.

It began as a fork adding the BGW320-505 as one more catalog entry. That did
not fit: upstream is deliberately DOCSIS-scoped, and supporting a fiber gateway
required changes to core status derivation, a new authentication strategy, and
optional device metadata — more than a catalog addition. Rather than push a
non-DOCSIS device into a DOCSIS project, this became a separate integration.

What changed here:

- Domain is `bgw320`; entities are `bgw320_*`.
- The catalog contains AT&T XGS-PON fiber gateways — currently the
  BGW320-505 and BGW620-700.
- Fiber link health is `pon_status`, not `docsis_status`.
- Downstream/upstream channel-count sensors are gone. XGS-PON has no DOCSIS
  channels, so they only ever reported 0.
- Channel-bond change notifications are gone; they are meaningless without
  channel bonding.
- Adds the `form_md5_nonce` auth strategy and per-request nonce injection for
  the restart action.

Because the engine packages are not published to PyPI under these changes, the
HACS artifact vendors them. See
[INSTALL.md](https://github.com/pope523/att-fiber-gateway/blob/main/INSTALL.md).

**Do not run both integrations at once.** They use different Home Assistant
domains, so Home Assistant itself is happy, but each bundles its own engine
under the same `solentlabs.*` import namespace. Whichever loads first wins for
both, and Python caches it — so this integration can silently end up running
upstream's DOCSIS catalog instead of its own. Remove `cable_modem_monitor`
before installing this one; see the migration steps in
[INSTALL.md](https://github.com/pope523/att-fiber-gateway/blob/main/INSTALL.md).

## Troubleshooting

- **No entities after setup.** Confirm `http://192.168.0.254` loads from the
  Home Assistant host. The gateway is HTTP-only on the LAN.
- **Restart button does nothing.** The access code is the 12-character code on
  the gateway label, not your Wi-Fi password or AT&T account password.
  Reconfigure the integration and re-enter it.
- **Optical temperature looks too high.** It is Celsius converted to your unit
  system; roughly 49 °C shows as about 120 °F, which is normal.
- **Diagnostics.** Settings → Devices & Services → AT&T BGW320 Gateway →
  Download diagnostics. Output is sanitized of IPs, paths, and credentials, but
  review before sharing.

More in
[docs/TROUBLESHOOTING.md](https://github.com/pope523/att-fiber-gateway/blob/main/docs/TROUBLESHOOTING.md).

## License

MIT. See
[LICENSE](https://github.com/pope523/att-fiber-gateway/blob/main/LICENSE) and
[docs/ATTRIBUTION.md](https://github.com/pope523/att-fiber-gateway/blob/main/docs/ATTRIBUTION.md).

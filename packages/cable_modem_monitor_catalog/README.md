# Device Catalog

[![CI](https://github.com/pope523/att-fiber-gateway/actions/workflows/tests.yml/badge.svg)](https://github.com/pope523/att-fiber-gateway/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Internal dependency of [AT&T BGW320 Gateway](https://github.com/pope523/att-fiber-gateway).**
> Not intended for direct use — install the HA integration via [HACS](https://hacs.xyz/).
>
> This package holds the device configuration, parser config, and test fixtures for
> the one device this integration targets. It is not published to PyPI; it is
> vendored into the HACS release artifact.

---

Auto-generated index of the device catalog.

**Data Sources:**

- `modem.yaml` — Single source of truth (manufacturer, model, hardware, ISPs, status)

**1 devices, 1 configurations** (1 ⏳ awaiting)

**Auth strategies:** none (1)

## Directory Structure

Each modem has a self-contained directory in the catalog package:

```text
packages/cable_modem_monitor_catalog/.../modems/
└── {manufacturer}/
    └── {model}/
        ├── modem.yaml           # Configuration, auth, hardware metadata
        ├── parser.yaml          # Declarative channel/system_info extraction
        ├── parser.py            # Optional PostProcessor for complex parsing
        └── test_data/           # HAR captures and golden files
            ├── modem.har
            └── modem.expected.json
```

## Supported Modems

| Manufacturer | Model | DOCSIS | Transport | Chipset | Auth | ISPs | Names | Status |
|--------------|-------|--------|-----------|---------|------|------|-------|--------|
| Nokia | [BGW320-505 (02001E0046004F)](https://github.com/solentlabs/cable_modem_monitor/blob/main/packages/cable_modem_monitor_catalog/solentlabs/cable_modem_monitor_catalog/modems/nokia/bgw320_505/modem.yaml) |  | ![HTML](https://img.shields.io/badge/-HTML-E34C26?style=flat-square "Standard web scraping") |  | ![none](https://img.shields.io/badge/-none-808080?style=flat-square "No Authentication") | [![ATT](https://img.shields.io/badge/-ATT-0091d5?style=flat-square "AT&T")](#att) | BGW320-505 | ⏳ Awaiting |

## Model Timeline

```text
```

_Timeline: █ = years actively supported, ░ = discontinued or not yet released_
_Scale: 2010-2026 (16 years)_

## Legend

- **Names**: All model names and part numbers that share this config (searchable)
- **Status**: ✅ Confirmed | ⏳ Awaiting Verification | 🚫 Unsupported
- **Transport**: ![HTML](https://img.shields.io/badge/-HTML-E34C26?style=flat-square) = web scraping | ![REST](https://img.shields.io/badge/-REST-5B9A5B?style=flat-square) = JSON REST API | [![HNAP](https://img.shields.io/badge/-HNAP-5B8FBF?style=flat-square)](https://en.wikipedia.org/wiki/Home_Network_Administration_Protocol) = SOAP-based, requires auth | ![CBN](https://img.shields.io/badge/-CBN-8B6914?style=flat-square) = CBN SOAP-based protocol
- **Auth**:
  - No auth: ![none](https://img.shields.io/badge/-none-808080?style=flat-square) No Authentication
  - Simple: ![basic](https://img.shields.io/badge/-basic-C07820?style=flat-square) Basic Authentication
  - Form-based: ![form](https://img.shields.io/badge/-form-4A7FB8?style=flat-square) Form Login | ![nonce](https://img.shields.io/badge/-nonce-3A6A9E?style=flat-square) Form Login (Nonce) | ![pbkdf2](https://img.shields.io/badge/-pbkdf2-4A9A5B?style=flat-square) Form Login (PBKDF2) | ![sjcl](https://img.shields.io/badge/-sjcl-7B4FB8?style=flat-square) Form Login (SJCL) | ![cbn](https://img.shields.io/badge/-cbn-8B6914?style=flat-square) Form Login CBN
  - Token-based: ![token](https://img.shields.io/badge/-token-0E9A8B?style=flat-square) URL Token | ![bearer](https://img.shields.io/badge/-bearer-1A7FAA?style=flat-square) Bearer Token
  - Protocol: ![hnap](https://img.shields.io/badge/-hnap-5B8FBF?style=flat-square) HNAP
  - Other: ![nonce](https://img.shields.io/badge/-nonce-9E9E9E?style=flat-square) Form Login (MD5 Nonce)

## Chipset Reference

| Chipset | Manufacturer | DOCSIS | Notes |
|---------|--------------|--------|-------|
| <span id="bcm33941ud"></span>[BCM33941UD](https://corporate.comcast.com/press/releases/comcast-broadcom-develop-ai-powered-access-network-pioneering-new-chipset) | Broadcom | 4.0 | Unified DOCSIS 4.0 FDX+ESD SoC. Co-developed with Comcast. Deployed in Xfinity XB10 (CGM601TCOM). |
| <span id="bcm3390"></span>[BCM3390](https://www.prnewswire.com/news-releases/broadcom-unleashes-gigabit-speeds-for-consumer-cable-modems-300016203.html) | Broadcom | 3.1 | Current flagship. 2x2 OFDM, 32x8 SC-QAM. Speeds exceeding 1 Gbps. |
| <span id="bcm3384"></span>[BCM3384](https://www.prnewswire.com/news-releases/broadcom-launches-gigabit-docsis-cable-gateway-family-186004842.html) | Broadcom | 3.0 | Reliable mid-tier. 16x4 or 24x8 channels. |
| <span id="bcm3383"></span>[BCM3383](https://www.prnewswire.com/news-releases/broadcom-launches-gigabit-docsis-cable-gateway-family-186004842.html) | Broadcom | 3.0 | Entry-level 8x4 chipset with integrated WiFi SoC. |
| <span id="bcm3380"></span>[BCM3380](https://www.webwire.com/ViewPressRel.asp?aId=92729) | Broadcom | 3.0 | Legacy 8x4 chipset. First single-chip DOCSIS 3.0 solution (2009). |
| <span id="puma-5"></span>[Puma 5](https://boxmatrix.info/wiki/Property:Puma5) | Intel | 3.0 | Legacy 8x4 chipset (TI TNETC4800). [Latency issues](https://www.theregister.com/2017/08/09/intel_puma_modem_woes/) less severe than Puma 6. |
| <span id="puma-6"></span>[Puma 6](https://boxmatrix.info/wiki/Property:Puma6) | Intel | 3.0 | ⚠️ **Avoid.** [Hardware flaw](https://www.theregister.com/2017/04/11/intel_puma_6_arris/) causes latency spikes up to 250ms under load. No fix available. |
| <span id="puma-7"></span>[Puma 7](https://boxmatrix.info/wiki/Property:Puma7) | Intel | 3.1 | ⚠️ **Avoid.** [Same architectural issues](https://www.theregister.com/2018/08/14/intel_puma_modem/) as Puma 6. Major vendors switched to Broadcom. |

## Provider Reference

| Code | Provider | Region | Approved Modems | Notes |
|------|----------|--------|-----------------|-------|
| <span id="comcast"></span>COM | Comcast Xfinity | US (nationwide) | [Official list](https://www.xfinity.com/support/articles/list-of-approved-cable-modems) | Online activation required |
| <span id="cox"></span>COX | Cox Communications | US (18 states) | [Official list](https://www.cox.com/residential/internet/learn/using-cox-compatible-modems.html) |  |
| <span id="spectrum"></span>SPEC | Spectrum (Charter) | US (41 states) | [Official list](https://www.spectrum.net/support/internet/compliant-modems-spectrum-network) | Formerly TWC, Bright House |
| <span id="twc"></span>TWC | Time Warner Cable | — | — | Merged into Spectrum (2016) |
| <span id="rogers"></span>ROG | Rogers | Canada | [Official list](https://www.rogers.com/) | No BYOM; Rogers equipment required |
| <span id="shaw"></span>SHAW | Shaw Communications | Canada (Western) | [Official list](https://www.shaw.ca/) | Merged with Rogers (2023) |
| <span id="videotron"></span>VID | Vidéotron | Canada (Quebec) | [Official list](https://www.videotron.com/) | Helix service requires leased equipment |
| <span id="volia"></span>VOLY | Volia | Ukraine | [Official list](https://en.wikipedia.org/wiki/Volia_(ISP)) | Acquired by Datagroup (2021) |
| <span id="pyür"></span>PYÜR | Pyür | Germany | [Official list](https://www.pyur.com/) | Formerly Tele Columbus |
| <span id="vodafone"></span>VDF | Vodafone Kabel | Germany | [Official list](https://www.vodafone.de/) | BYOM allowed since 2016; absorbed Unitymedia |
| <span id="unitymedia"></span>UM | Unitymedia | Germany (West) | — | Merged into Vodafone (2019) |
| <span id="virgin"></span>VM | Virgin Media | UK | [Official list](https://www.virginmedia.com/) | No BYOM; modem mode available |
| <span id="telia"></span>TEL | Telia | Nordic/Baltic | [Official list](https://www.teliacompany.com/) | Sweden, Finland, Norway, Baltics |
| <span id="mediacom"></span>MED | Mediacom | US (Midwest/South) | [Official list](https://mediacomcable.com/compatible-retail-modems/) |  |
| <span id="suddenlink"></span>SUD | Suddenlink (Optimum) | US (13 states) | — | Rebranded to Optimum (Aug 2022); Altice USA subsidiary. Source: <https://en.wikipedia.org/wiki/Suddenlink_Communications> |
| <span id="rcn"></span>RCN | Astound (formerly RCN) | US (Northeast) | [Official list](https://www.astound.com/support/internet/bring-your-own-modem/) | No official list; DOCSIS 3.1 recommended |
| <span id="cableone"></span>C1 | Sparklight (Cable One) | US (21 states) | [Official list](https://support.sparklight.com/hc/en-us/articles/115009158227-Supported-Modems-Residential-Only) | DOCSIS 3.1 required |
| <span id="kood"></span>KOOD | Koodo | Canada | — | Telus subsidiary |
| <span id="brighthouse"></span>BRIG | BrightHouse Networks | US (Southeast) | — | Merged into Spectrum (2016). Source: <https://en.wikipedia.org/wiki/Bright_House_Networks> |
| <span id="service-electric"></span>SERV | Service Electric Cablevision | US (Pennsylvania) | [Official list](https://www.sectv.com/) | Family-owned regional ISP since 1948. Source: <https://en.wikipedia.org/wiki/Service_Electric> |
| <span id="teksavvy"></span>TEKS | Teksavvy | Canada | [Official list](https://teksavvy.com/services/internet/) | Independent Canadian ISP/reseller. Source: <https://en.wikipedia.org/wiki/TekSavvy> |
| <span id="att"></span>ATT | AT&T | US (21 states) | [Official list](https://www.att.com/internet/fiber/) | Fiber (XGS-PON) and DSL; gateways are ISP-supplied (no BYOD). BGW320-505 is a Nokia ONT+router. Source: <https://en.wikipedia.org/wiki/AT%26T_Internet> |

---

Generated by `scripts/generate_catalog_index.py` from 1 modem configs ([source](https://github.com/solentlabs/cable_modem_monitor/blob/main/packages/cable_modem_monitor_catalog/scripts/generate_catalog_index.py)).

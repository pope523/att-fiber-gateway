# Attribution and Credits

## Upstream project

This integration is derived from
**[solentlabs/cable_modem_monitor](https://github.com/solentlabs/cable_modem_monitor)**
by **Ken Schulz** (@kwschulz), MIT licensed.

Nearly all of the collection, parsing, authentication, and orchestration
machinery here is that project's work. What this repository adds is the
BGW320-505 and BGW620-700 device definitions, fiber-specific status
handling, the `form_md5_nonce` auth strategy, and the rescoping of the
Home Assistant adapter to AT&T fiber gateways.

The upstream copyright notice is retained in [LICENSE](../LICENSE) as the MIT
license requires. If you want DOCSIS cable modem monitoring, use the upstream
project — it supports a large catalog of modems and is actively maintained.

## Device research

Understanding the BGW320's web interface was informed by prior
reverse-engineering of AT&T residential gateways:

| Project | Used for |
|---|---|
| [edgan/att-fiber-gateway-info](https://github.com/edgan/att-fiber-gateway-info) | Page inventory and the nonce + MD5 login flow |
| [attrouter](https://github.com/0x666690/attrouter) | Reboot endpoint and form-field behaviour |

Both are related prior art: they informed the approach, and the login and
restart flows here were then confirmed directly against the hardware (firmware
6.34.7) before being implemented in this project's own architecture.

The `1/10 dBm` scaling for optical power comes from the gateway's own on-page
help text, not from external sources.

## Fixtures

The HAR fixtures under
`packages/cable_modem_monitor_catalog/solentlabs/cable_modem_monitor_catalog/modems/nokia/bgw320_505/test_data/`
were captured from a live BGW320-505 and sanitized: serial numbers, MAC
addresses, public IP addresses, and session nonces are replaced with the
catalog-safe placeholder values defined in
`packages/cable_modem_monitor_catalog/scripts/data/pii_safe_values.json`.

The HAR fixtures under
`packages/cable_modem_monitor_catalog/solentlabs/cable_modem_monitor_catalog/modems/commscope/bgw620_700/test_data/`
were captured from a live BGW620-700 and sanitized the same way, contributed
by [@MatthewPricePhd](https://github.com/MatthewPricePhd).

## Dependencies

- [Home Assistant Core](https://github.com/home-assistant/core) — integration framework
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [pydantic](https://docs.pydantic.dev/) — config model validation
- [requests](https://requests.readthedocs.io/) — HTTP transport
- [PyYAML](https://pyyaml.org/) — device and parser config
- [defusedxml](https://github.com/tiran/defusedxml) — safe XML parsing
- [cryptography](https://cryptography.io/) — retained for engine auth strategies

Development: [pytest](https://pytest.org/),
[pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component),
[ruff](https://github.com/astral-sh/ruff), [black](https://black.readthedocs.io/),
[mypy](https://mypy-lang.org/).

## Attribution notes

This project was developed with AI assistance. Citations above were checked
against the actual work: the two device-research projects were genuinely
consulted while mapping the gateway's pages and login flow, and their influence
is described with deliberately conservative framing ("informed by", "related
prior art") because the implementation is independent and the protocol details
were verified against real hardware rather than copied.

If your work is used here without proper credit, please open an issue — it was
not intentional and will be corrected.

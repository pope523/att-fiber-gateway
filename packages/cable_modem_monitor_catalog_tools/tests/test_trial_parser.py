"""Tests for trial parser — validates dry-run extraction.

The trial parser feeds HAR data through the real ModemParserCoordinator
with a candidate parser.yaml to verify extraction works.
"""

from __future__ import annotations

import pytest
import yaml
from solentlabs.cable_modem_monitor_catalog import CATALOG_PATH
from solentlabs.cable_modem_monitor_catalog_tools.trial_parser import TrialResult, trial_parse

# The catalog holds a single device: the AT&T Nokia BGW320-505, an XGS-PON
# fiber gateway. It is auth:none and channel-less — it has no DOCSIS
# downstream/upstream channels, so everything is surfaced via system_info.
_BGW320_DIR = CATALOG_PATH / "nokia" / "bgw320_505"
_BGW320_HAR = str(_BGW320_DIR / "test_data" / "modem.har")
_BGW320_PARSER = (_BGW320_DIR / "parser.yaml").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _allow_sockets(socket_enabled: None) -> None:  # noqa: ARG001
    """Enable sockets (trial parser loads HAR resources)."""


class TestTrialParseSuccess:
    """Verify trial_parse succeeds on known-good config."""

    def test_passed(self) -> None:
        """BGW320-505 trial parse passes despite having no channels."""
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        assert result.passed is True

    def test_channel_counts(self) -> None:
        """BGW320-505 is channel-less: no DOCSIS downstream/upstream."""
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        assert result.channel_counts["downstream"] == 0
        assert result.channel_counts["upstream"] == 0

    def test_system_info_fields(self) -> None:
        """BGW320-505 extracts device, fiber, and WAN system_info fields."""
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        assert "system_uptime" in result.system_info_fields
        assert "hardware_version" in result.system_info_fields
        assert "software_version" in result.system_info_fields
        # Fiber-specific fields replace the DOCSIS channel view.
        assert "pon_status" in result.system_info_fields
        assert "optical_status" in result.system_info_fields
        assert "wan_link_speed_mbps" in result.system_info_fields

    def test_no_errors(self) -> None:
        """A channel-less parser produces no hard errors.

        Regression guard: section detection must be structural. This
        parser.yaml mentions "downstream/upstream" only in a comment
        explaining that the device has none, and a substring match
        against the raw text reported phantom "extracted 0 channels"
        errors.
        """
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        assert result.errors == []

    def test_golden_file_has_system_info(self) -> None:
        """Golden file carries the extracted fiber/WAN values."""
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        system_info = result.golden_file.get("system_info", {})
        assert system_info["software_version"]
        assert system_info["pon_status"] == "Operational"


class TestTrialParseFailure:
    """Verify trial_parse reports errors for bad configs."""

    def test_invalid_yaml(self) -> None:
        """Invalid parser.yaml produces errors."""
        result = trial_parse(_BGW320_HAR, "not: a: valid: parser")
        assert result.passed is False
        assert len(result.errors) > 0

    def test_wrong_label_drops_field(self) -> None:
        """A label that matches nothing on the page yields no value."""
        bad_parser = _BGW320_PARSER.replace(
            'label: "Software Version"',
            'label: "NonexistentLabel"',
        )
        result = trial_parse(_BGW320_HAR, bad_parser)
        assert "software_version" not in result.system_info_fields

    def test_declared_channel_section_with_no_channels_errors(self) -> None:
        """Declaring a downstream section that extracts nothing is an error.

        Complements ``test_no_errors``: the check is not simply disabled
        for channel-less devices — it still fires when the config really
        does declare a channel section.
        """
        parsed = yaml.safe_load(_BGW320_PARSER)
        parsed["downstream"] = {
            "sources": [
                {
                    "format": "html_table",
                    "resource": "/cgi-bin/sysinfo.ha",
                    "selector": {"match": "NonexistentTable"},
                    "columns": {},
                }
            ]
        }
        result = trial_parse(_BGW320_HAR, yaml.safe_dump(parsed))
        assert result.passed is False
        assert any("Downstream" in err for err in result.errors)


class TestTrialResultDataclass:
    """Verify TrialResult structure."""

    def test_result_type(self) -> None:
        """trial_parse returns a TrialResult."""
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        assert isinstance(result, TrialResult)

    def test_golden_file_is_dict(self) -> None:
        """golden_file is a dict with expected keys."""
        result = trial_parse(_BGW320_HAR, _BGW320_PARSER)
        assert isinstance(result.golden_file, dict)
        assert "downstream" in result.golden_file
        assert "upstream" in result.golden_file
        assert "system_info" in result.golden_file

"""Trial parser — validates extraction before writing config.

Feeds HAR response bodies through Core's ``ModemParserCoordinator``
with a candidate ``parser.yaml`` config to verify that selectors find
the right tables and field mappings produce non-empty values.

This is the "dry run" step — it catches bad selectors, wrong column
indices, or misclassified formats before the config is committed.

Usage::

    from cable_modem_monitor_catalog_tools.trial_parser import trial_parse

    result = trial_parse(har_path, parser_yaml_content)
    if result.errors:
        print("Extraction failed:", result.errors)
    else:
        print(f"DS: {result.channel_counts['downstream']} channels")
        print(f"System info: {result.system_info_fields}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml
from solentlabs.cable_modem_monitor_catalog_tools.generate_golden_file import (
    generate_golden_file,
)


@dataclass
class TrialResult:
    """Result of a trial parse run.

    Attributes:
        passed: True if extraction produced meaningful data with no errors.
        golden_file: The extracted ModemData dict.
        channel_counts: Downstream and upstream channel counts.
        system_info_fields: Field names present in system_info.
        errors: Hard errors that prevented extraction.
        warnings: Soft issues (empty fields, unexpected values).
    """

    passed: bool
    golden_file: dict[str, Any]
    channel_counts: dict[str, int] = field(default_factory=dict)
    system_info_fields: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def trial_parse(
    har_path: str,
    parser_yaml_content: str,
) -> TrialResult:
    """Run a trial extraction and validate results.

    Feeds the HAR through ``generate_golden_file`` (which uses the
    same ``ModemParserCoordinator`` as production), then checks for
    empty sections, zero channels, and missing system_info fields.

    Args:
        har_path: Path to the HAR file.
        parser_yaml_content: Candidate parser.yaml as a YAML string.

    Returns:
        ``TrialResult`` with pass/fail, extracted data, and diagnostics.
    """
    result = generate_golden_file(har_path, parser_yaml_content)

    errors = list(result.errors)
    warnings: list[str] = []
    golden = result.golden_file

    # Check for empty extraction
    ds_count = result.channel_counts.get("downstream", 0)
    us_count = result.channel_counts.get("upstream", 0)

    sections = _declared_sections(parser_yaml_content)

    if ds_count == 0 and "downstream" in sections:
        errors.append("Downstream section defined but extracted 0 channels")
    if us_count == 0 and "upstream" in sections:
        errors.append("Upstream section defined but extracted 0 channels")

    # Validate channel field coverage
    _check_channel_fields(golden.get("downstream", []), "downstream", warnings)
    _check_channel_fields(golden.get("upstream", []), "upstream", warnings)

    # Validate system_info
    system_info = golden.get("system_info", {})
    if "system_info" in sections and not system_info:
        warnings.append("system_info section defined but extracted no fields")
    for field_name, value in system_info.items():
        if value is None or value == "":
            warnings.append(f"system_info.{field_name} is empty")

    # A parser passes when it hit no errors and actually extracted
    # something. Channels are not required: fiber ONT/gateways are
    # channel-less and legitimately surface everything via system_info.
    extracted_anything = ds_count + us_count > 0 or bool(system_info)
    passed = len(errors) == 0 and extracted_anything

    return TrialResult(
        passed=passed,
        golden_file=golden,
        channel_counts=result.channel_counts,
        system_info_fields=result.system_info_fields,
        errors=errors,
        warnings=warnings,
    )


def _declared_sections(parser_yaml_content: str) -> frozenset[str]:
    """Return the top-level section names the parser config declares.

    Parsed structurally rather than substring-matched against the raw
    text: a parser.yaml whose *comments* mention "downstream" (as a
    channel-less fiber config naturally does when explaining that it has
    none) would otherwise be reported as declaring a downstream section
    and fail with "extracted 0 channels".

    Malformed YAML yields an empty set; ``generate_golden_file`` already
    surfaces the parse failure as a hard error.
    """
    try:
        parsed = yaml.safe_load(parser_yaml_content)
    except yaml.YAMLError:
        return frozenset()
    if not isinstance(parsed, dict):
        return frozenset()
    return frozenset(str(key) for key in parsed)


def _check_channel_fields(
    channels: list[dict[str, Any]],
    direction: str,
    warnings: list[str],
) -> None:
    """Check that extracted channels have non-empty core fields."""
    if not channels:
        return

    core_fields = ("channel_id", "frequency", "power")
    for i, channel in enumerate(channels[:3]):
        for fname in core_fields:
            if fname in channel and (channel[fname] is None or channel[fname] == ""):
                warnings.append(f"{direction}[{i}].{fname} is empty")

"""Tests for parser_sandbox — AST-based static analysis for parser.py.

Table-driven: each case is (source, expected violation count, expected
substring in first violation message). The anti-fragile suite validates
that every existing catalog parser.py passes the sandbox.
"""

from pathlib import Path

import pytest
from solentlabs.cable_modem_monitor_core.validation.parser_sandbox import (
    ALLOWED_MODULES,
    SandboxViolation,
    validate_parser_sandbox,
)

# ---------------------------------------------------------------------------
# Catalog root — for anti-fragile existing-parser checks
# ---------------------------------------------------------------------------

_CATALOG_MODEMS = (
    Path(__file__).resolve().parents[4]
    / "packages"
    / "cable_modem_monitor_catalog"
    / "solentlabs"
    / "cable_modem_monitor_catalog"
    / "modems"
)

# ---------------------------------------------------------------------------
# Valid sources — zero violations expected
# ---------------------------------------------------------------------------

_VALID_SOURCES = [
    pytest.param("class PostProcessor:\n    pass\n", id="empty-class"),
    pytest.param("from __future__ import annotations\n", id="future-annotations"),
    pytest.param("import re\n", id="import-re"),
    pytest.param("import math\n", id="import-math"),
    pytest.param("import json\n", id="import-json"),
    pytest.param("import datetime\n", id="import-datetime"),
    pytest.param("import collections\n", id="import-collections"),
    pytest.param("import functools\n", id="import-functools"),
    pytest.param("import itertools\n", id="import-itertools"),
    pytest.param("from typing import Any\n", id="from-typing"),
    pytest.param("from bs4 import Tag\n", id="from-bs4"),
    pytest.param("from json import loads\n", id="from-json-loads"),
    pytest.param(
        "from __future__ import annotations\nimport re\nfrom typing import Any\n",
        id="typical-parser-imports",
    ),
    pytest.param(
        "x = [1, 2, 3]\ny = x.remove(1)\n",
        id="remove-on-list-not-flagged",
    ),
]


@pytest.mark.parametrize("source", _VALID_SOURCES)
def test_valid_source(source: str) -> None:
    """Valid parser.py sources produce zero violations."""
    assert validate_parser_sandbox(source) == []


# ---------------------------------------------------------------------------
# Forbidden imports — one violation per bad import
# ---------------------------------------------------------------------------

_FORBIDDEN_IMPORTS = [
    pytest.param("import os\n", "os", id="import-os"),
    pytest.param("import subprocess\n", "subprocess", id="import-subprocess"),
    pytest.param("import requests\n", "requests", id="import-requests"),
    pytest.param("import pathlib\n", "pathlib", id="import-pathlib"),
    pytest.param("import sys\n", "sys", id="import-sys"),
    pytest.param("import urllib\n", "urllib", id="import-urllib"),
    pytest.param("from pathlib import Path\n", "from pathlib", id="from-pathlib"),
    pytest.param(
        "from urllib.request import urlopen\n",
        "from urllib",
        id="from-urllib-request",
    ),
    pytest.param("from os.path import join\n", "from os", id="from-os-path"),
]


@pytest.mark.parametrize("source, expected_substr", _FORBIDDEN_IMPORTS)
def test_forbidden_import(source: str, expected_substr: str) -> None:
    """Forbidden imports produce exactly one violation."""
    violations = validate_parser_sandbox(source)
    assert len(violations) == 1
    assert expected_substr in violations[0].message


# ---------------------------------------------------------------------------
# Forbidden function calls
# ---------------------------------------------------------------------------

_FORBIDDEN_CALLS = [
    pytest.param('eval("1+1")\n', "eval", id="eval"),
    pytest.param('exec("pass")\n', "exec", id="exec"),
    pytest.param('open("file.txt")\n', "open", id="open"),
    pytest.param('compile("pass", "", "exec")\n', "compile", id="compile"),
    pytest.param('__import__("os")\n', "__import__", id="dunder-import"),
]


@pytest.mark.parametrize("source, expected_substr", _FORBIDDEN_CALLS)
def test_forbidden_function(source: str, expected_substr: str) -> None:
    """Forbidden function calls produce exactly one violation."""
    violations = validate_parser_sandbox(source)
    assert len(violations) == 1
    assert expected_substr in violations[0].message


# ---------------------------------------------------------------------------
# Relative imports
# ---------------------------------------------------------------------------

_RELATIVE_IMPORTS = [
    pytest.param("from . import foo\n", id="from-dot"),
    pytest.param("from .. import bar\n", id="from-dotdot"),
    pytest.param("from .utils import helper\n", id="from-dot-utils"),
]


@pytest.mark.parametrize("source", _RELATIVE_IMPORTS)
def test_relative_import(source: str) -> None:
    """Relative imports are forbidden."""
    violations = validate_parser_sandbox(source)
    assert len(violations) == 1
    assert "Relative import" in violations[0].message


# ---------------------------------------------------------------------------
# Multiple violations in one source
# ---------------------------------------------------------------------------


def test_multiple_violations() -> None:
    """Source with multiple problems reports all of them."""
    source = 'import os\nimport subprocess\neval("x")\n'
    violations = validate_parser_sandbox(source)
    assert len(violations) == 3


# ---------------------------------------------------------------------------
# Syntax errors
# ---------------------------------------------------------------------------


def test_syntax_error() -> None:
    """Syntax errors are reported as violations."""
    violations = validate_parser_sandbox("def foo(\n")
    assert len(violations) == 1
    assert "Syntax error" in violations[0].message


# ---------------------------------------------------------------------------
# SandboxViolation.__str__
# ---------------------------------------------------------------------------


def test_violation_str() -> None:
    """__str__ formats as 'line:col - message'."""
    v = SandboxViolation(line=10, col=4, message="bad import")
    assert str(v) == "10:4 — bad import"


# ---------------------------------------------------------------------------
# Anti-fragile: every existing catalog parser.py must pass
# ---------------------------------------------------------------------------


def test_existing_catalog_parsers_pass() -> None:
    """Every parser.py in the catalog passes the sandbox.

    This is the anti-fragile check — if we tighten the whitelist and
    break an existing parser, this test catches it before CI does.
    """
    if not _CATALOG_MODEMS.is_dir():
        pytest.skip("Catalog not found (editable install required)")

    parser_files = list(_CATALOG_MODEMS.rglob("parser.py"))
    assert parser_files, "Expected at least one parser.py in catalog"

    failures: list[str] = []
    for p in parser_files:
        violations = validate_parser_sandbox(p.read_text(encoding="utf-8"))
        for v in violations:
            failures.append(f"{p.relative_to(_CATALOG_MODEMS)}: {v}")

    assert failures == [], "Sandbox violations in catalog:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# ALLOWED_MODULES is a frozenset (immutable)
# ---------------------------------------------------------------------------


def test_allowed_modules_immutable() -> None:
    """ALLOWED_MODULES cannot be mutated at runtime."""
    assert isinstance(ALLOWED_MODULES, frozenset)

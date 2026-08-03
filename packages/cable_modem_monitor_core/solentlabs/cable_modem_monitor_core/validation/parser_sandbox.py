"""Parser Sandbox — static analysis for parser.py.

Enforces the "parser only parses" principle by validating that
parser.py only uses allowed imports and performs no I/O, network, or
process operations.

See PARSING_SPEC.md Sandbox Rules section.
"""

import ast
from dataclasses import dataclass


@dataclass
class SandboxViolation:
    """A violation of the parser sandbox rules.

    Attributes:
        line: 1-based line number of the violation.
        col: 0-based column offset.
        message: Human-readable explanation of the rule violated.
    """

    line: int
    col: int
    message: str

    def __str__(self) -> str:
        return f"{self.line}:{self.col} — {self.message}"


# Whitelist of top-level modules that parser.py is allowed to import.
# Any import outside this list is a sandbox violation, except for the
# fully-qualified Core-public helpers in ALLOWED_FULL_MODULES below.
# __future__ is always allowed (syntax/behavior changes, not runtime).
ALLOWED_MODULES = frozenset(
    {
        "__future__",
        "math",
        "re",
        "json",
        "datetime",
        "bs4",  # BeautifulSoup
        "typing",
        "collections",
        "functools",
        "itertools",
    }
)

# Fully-qualified Core module paths that parser.py may import. This
# is the ONLY way for parser.py to consume Core code — every entry
# is a deliberate, audited public-helper surface. See
# ``post_processor_helpers.py`` for the conventions when adding a
# helper.
ALLOWED_FULL_MODULES = frozenset(
    {
        "solentlabs.cable_modem_monitor_core.post_processor_helpers",
    }
)

# Functions that are explicitly forbidden even if they belong to
# allowed modules (e.g., executing code).
FORBIDDEN_FUNCTIONS = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",  # Built-in open() for I/O
    }
)


class _ParserSandboxValidator(ast.NodeVisitor):
    """AST visitor that identifies sandbox violations in parser.py."""

    def __init__(self) -> None:
        self.violations: list[SandboxViolation] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        """Check for non-whitelisted 'import x' statements."""
        for alias in node.names:
            name = alias.name.split(".")[0]
            if name not in ALLOWED_MODULES:
                self._add_violation(node, f"Forbidden import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        """Check for non-whitelisted 'from x import y' statements."""
        if node.level > 0:
            self._add_violation(node, "Relative imports are forbidden")
            return

        if node.module:
            if node.module in ALLOWED_FULL_MODULES:
                self.generic_visit(node)
                return
            name = node.module.split(".")[0]
            if name not in ALLOWED_MODULES:
                self._add_violation(
                    node,
                    f"Forbidden import: 'from {node.module} import ...'",
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        """Check for forbidden built-in functions."""
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_FUNCTIONS:
            self._add_violation(node, f"Forbidden function call: '{node.func.id}()'")
        self.generic_visit(node)

    def _add_violation(self, node: ast.AST, message: str) -> None:
        """Record a sandbox violation."""
        self.violations.append(
            SandboxViolation(
                line=getattr(node, "lineno", 0),
                col=getattr(node, "col_offset", 0),
                message=message,
            )
        )


def validate_parser_sandbox(source: str) -> list[SandboxViolation]:
    """Validate that parser.py source code adheres to sandbox rules.

    Args:
        source: The Python source code of parser.py.

    Returns:
        List of SandboxViolation objects. Empty means the source is
        considered "safe" by the static analyzer.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            SandboxViolation(
                line=exc.lineno or 0,
                col=exc.offset or 0,
                message=f"Syntax error: {exc.msg}",
            )
        ]

    validator = _ParserSandboxValidator()
    validator.visit(tree)
    return validator.violations

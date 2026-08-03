"""Curated helpers callable from per-modem ``parser.py`` PostProcessors.

The parser-sandbox validator forbids ``parser.py`` from importing
arbitrary Core internals — that's what keeps PostProcessors honest
(no I/O, no auth bypass, no peeking into orchestrator state). But
some declaratively-extracted primitives are genuinely useful inside
PostProcessors when a firmware quirk can't be expressed in
parser.yaml alone.

This module is the **only** Core surface ``parser.py`` may import.
The sandbox allowlists this exact module path; everything re-exported
here is reviewed for parser.py safety.

Adding a helper:

1. Import or define the function here.
2. Append to ``__all__`` so the public surface is explicit.
3. (No sandbox change needed — the allowlist already covers this
   module.)

Removing or renaming a helper is a breaking change for catalog
parser.py files. Keep churn low.
"""

from __future__ import annotations

from .parsers.formats.json_transposed import transpose_indexed_rows

__all__ = ["transpose_indexed_rows"]

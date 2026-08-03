#!/usr/bin/env bash
# Bans <sub>, <small>, and similar HTML tags in markdown files.
#
# These tags have no legitimate use in this project's documentation.
# When they appear, they are wrapping italic/bold text purely to
# evade MD036 (emphasis-as-heading) — a markdownlint shortcut that
# defeats the rule's intent. Past sessions have repeatedly reached
# for this pattern; this hook exists because the principle "no
# exclusions for bad documentation" was being eroded one
# "legitimate use case" at a time.
#
# To fix a violation, restructure the content. Do NOT:
#   - Wrap the tag differently to dodge this check
#   - Add the tag to the MD033 allowlist in .markdownlint.jsonc
#   - Add the tag to BANNED_TAGS' opposite (no exemption mechanism
#     exists; that is intentional)
#
# Restructure options:
#   - Drop the emphasis (taglines and footers read fine as plain text)
#   - Convert to a real heading if the line IS a section label
#   - Add surrounding text so it is not standalone emphasis
#
# Pre-commit usage: passes staged .md files as args.
# Manual usage: ./scripts/dev/check-md-no-emphasis-evasion.sh

set -euo pipefail

BANNED_TAGS=("sub" "small")

# Files to check. If args provided (pre-commit mode), use them.
# Otherwise scan all tracked .md files.
if [[ $# -gt 0 ]]; then
    files=("$@")
else
    mapfile -t files < <(git ls-files '*.md')
fi

violations=0
for f in "${files[@]}"; do
    [[ -f "$f" ]] || continue

    # Build alternation pattern: <sub>|<small>
    pattern=""
    for tag in "${BANNED_TAGS[@]}"; do
        [[ -n "$pattern" ]] && pattern+="|"
        pattern+="<${tag}[ >]"
    done

    matches=$(grep -nE "$pattern" "$f" || true)
    if [[ -n "$matches" ]]; then
        if [[ $violations -eq 0 ]]; then
            echo "ERROR: HTML emphasis-evasion detected in markdown:" >&2
            echo "" >&2
        fi
        echo "  $f:" >&2
        # Indent each match line for readability
        while IFS= read -r line; do
            echo "    $line" >&2
        done <<< "$matches"
        violations=$((violations + 1))
    fi
done

if [[ $violations -gt 0 ]]; then
    echo "" >&2
    echo "Banned tags: ${BANNED_TAGS[*]}" >&2
    echo "" >&2
    echo "These tags wrap italic/bold text to dodge MD036" >&2
    echo "(emphasis-as-heading). They have no legitimate use in this" >&2
    echo "project's documentation. Restructure the content:" >&2
    echo "" >&2
    echo "  - Drop the emphasis (taglines and footers read fine as plain text)" >&2
    echo "  - Convert to a real heading if the line IS a section label" >&2
    echo "  - Add surrounding text so it is not standalone emphasis" >&2
    echo "" >&2
    echo "Do NOT 'fix' this by:" >&2
    echo "  - Adding the tag to .markdownlint.jsonc allowed_elements" >&2
    echo "    (that is the same evasion shape, one layer up)" >&2
    echo "  - Removing the tag from BANNED_TAGS in this script" >&2
    echo "    (no exemption mechanism exists; it is not an oversight)" >&2
    exit 1
fi

exit 0

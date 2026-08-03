#!/bin/bash
# Setup script to configure git with a privacy-safe email address
# This helps protect contributor privacy by using GitHub's noreply email
#
# Usage:
#   ./scripts/dev/setup-git-email.sh           # Interactive setup
#   ./scripts/dev/setup-git-email.sh --check   # Check only (for CI/pre-commit)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current email
CURRENT_EMAIL=$(git config user.email 2>/dev/null || echo "")

# Allowed email patterns
is_allowed_email() {
  local email="$1"
  if [[ "$email" =~ @users\.noreply\.github\.com$ ]]; then
    return 0
  elif [[ "$email" == "noreply@anthropic.com" ]]; then
    return 0
  elif [[ "$email" == "noreply@github.com" ]]; then
    return 0
  fi
  return 1
}

# Check-only mode (for pre-commit hook)
if [[ "$1" == "--check" ]]; then
  if is_allowed_email "$CURRENT_EMAIL"; then
    exit 0
  else
    echo ""
    echo -e "${YELLOW}============================================================${NC}"
    echo -e "${YELLOW}  WARNING: Personal email detected in git config${NC}"
    echo -e "${YELLOW}============================================================${NC}"
    echo ""
    echo -e "  Current email: ${RED}$CURRENT_EMAIL${NC}"
    echo ""
    echo "  Run this to fix: ./scripts/dev/setup-git-email.sh"
    echo "  Or VS Code task: 'Setup Git Email Privacy'"
    echo ""
    exit 1
  fi
fi

# Interactive mode
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Git Email Privacy Setup${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

if [[ -z "$CURRENT_EMAIL" ]]; then
  echo -e "${YELLOW}No git email configured.${NC}"
elif is_allowed_email "$CURRENT_EMAIL"; then
  echo -e "${GREEN}✓ Your git email is already privacy-safe:${NC}"
  echo -e "  $CURRENT_EMAIL"
  echo ""
  echo "No changes needed!"
  exit 0
else
  echo -e "${YELLOW}⚠ Current git email is a personal address:${NC}"
  echo -e "  ${RED}$CURRENT_EMAIL${NC}"
fi

echo ""
echo -e "${BLUE}To protect your privacy, use GitHub's noreply email.${NC}"
echo ""
echo "Steps:"
echo "  1. Go to: https://github.com/settings/emails"
echo "  2. Check 'Keep my email addresses private'"
echo "  3. Copy your noreply email (looks like: 12345678+username@users.noreply.github.com)"
echo ""

# Prompt for email
read -p "Paste your GitHub noreply email (or press Enter to skip): " NEW_EMAIL

if [[ -z "$NEW_EMAIL" ]]; then
  echo ""
  echo -e "${YELLOW}Skipped. You can run this again later.${NC}"
  exit 0
fi

# Validate the email looks like a noreply
if ! is_allowed_email "$NEW_EMAIL"; then
  echo ""
  echo -e "${RED}Error: That doesn't look like a GitHub noreply email.${NC}"
  echo "Expected format: 12345678+username@users.noreply.github.com"
  exit 1
fi

# Configure git
git config user.email "$NEW_EMAIL"

echo ""
echo -e "${GREEN}✓ Git email configured successfully!${NC}"
echo -e "  New email: ${GREEN}$NEW_EMAIL${NC}"
echo ""
echo "This setting applies to this repository only."
echo "Your commits will now use this privacy-safe email."
echo ""

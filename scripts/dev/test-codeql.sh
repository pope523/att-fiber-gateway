#!/bin/bash
# Script to test CodeQL queries locally
#
# This script runs CodeQL query tests to validate custom security queries.
# It should be run from anywhere in the project.
#
# Exit codes:
#   0: All tests passed
#   1: Tests failed or CodeQL CLI not found

set -e

# Get the project root directory (two levels up from scripts/dev/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

CODEQL_BIN="$PROJECT_ROOT/codeql/codeql"

# Check if CodeQL is installed
if [ ! -f "$CODEQL_BIN" ]; then
    echo "Error: CodeQL CLI not found at $CODEQL_BIN"
    echo ""
    echo "To install CodeQL CLI:"
    echo "  cd $PROJECT_ROOT"
    echo "  wget https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip"
    echo "  unzip codeql-linux64.zip && rm codeql-linux64.zip"
    echo "  cd cable-modem-monitor-ql && ../codeql/codeql pack install"
    exit 1
fi

echo "Testing CodeQL queries..."
echo ""

# Test the query unit tests
echo "Running query unit tests..."
$CODEQL_BIN test run cable-modem-monitor-ql/tests/

echo ""
echo "Running query validation tests..."
$CODEQL_BIN test run cable-modem-monitor-ql/queries/

echo ""
echo "✅ All CodeQL tests passed!"

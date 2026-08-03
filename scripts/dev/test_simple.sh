#!/bin/bash
# Simple test runner - no virtual environment required
#
# Use this when:
#   - You don't want to use a virtual environment
#   - You're running in CI or a container
#   - You prefer global or user-space installations
#
# For isolated development with venv, use run_tests_local.sh instead

set -e

echo "=========================================="
echo "Cable Modem Monitor - Simple Test Runner"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Installing test dependencies..."
    pip3 install --user -r tests/requirements.txt
    echo ""
fi

# Run tests
echo "Running tests..."
echo ""
pytest tests/ -v --tb=short

echo ""
echo "✓ All tests passed!"

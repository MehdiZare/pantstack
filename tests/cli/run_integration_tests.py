#!/usr/bin/env python3
"""Runner script for integration tests that need filesystem access."""

import sys
import pytest

def main():
    """Run integration tests with filesystem access."""
    sys.exit(pytest.main([
        "tests/cli/test_service_lifecycle.py",
        "-v",
        "--tb=short",
    ]))

if __name__ == "__main__":
    main()
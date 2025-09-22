"""CLI testing infrastructure with automatic cleanup."""

from .cleanup import TestCleanupManager, assert_no_test_artifacts, cleanup_after_test

__all__ = [
    "TestCleanupManager",
    "cleanup_after_test",
    "assert_no_test_artifacts",
]

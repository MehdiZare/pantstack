"""Service library modules."""

from .modules.testmodule import TestmoduleModule

# Module registry for service discovery
MODULES = [
    TestmoduleModule(),
]

__all__ = ["MODULES", "TestmoduleModule"]

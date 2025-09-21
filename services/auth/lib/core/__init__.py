"""Core infrastructure for auth service."""

from .config import AuthConfig
from .container import ApplicationContainer

__all__ = ["AuthConfig", "ApplicationContainer"]
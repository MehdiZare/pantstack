"""Database client for auth service."""

from typing import Optional

from supabase import Client, create_client

from shared.core.config import DatabaseConfig


def get_supabase_client(config: DatabaseConfig) -> Optional[Client]:
    """Get Supabase client instance.

    Args:
        config: Database configuration

    Returns:
        Supabase client or None if not configured
    """
    if not config.is_configured:
        print("⚠️ Supabase not configured, using mock client")
        return None

    client = create_client(
        config.supabase_url,
        config.supabase_anon_key,
    )

    return client


class SupabaseClient:
    """Wrapper for Supabase client with additional functionality."""

    def __init__(self, config: DatabaseConfig):
        """Initialize Supabase client wrapper.

        Args:
            config: Database configuration
        """
        self.config = config
        self._client = get_supabase_client(config)

    @property
    def client(self) -> Optional[Client]:
        """Get the underlying Supabase client."""
        return self._client

    def table(self, name: str):
        """Get a table reference.

        Args:
            name: Table name

        Returns:
            Table reference or mock
        """
        if self._client:
            return self._client.table(name)
        else:
            # Return a mock for development
            return MockTable(name)

    async def execute_query(self, query: str, params: dict = None):
        """Execute a raw SQL query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query result
        """
        if self._client:
            return self._client.rpc(query, params or {})
        else:
            return {"data": [], "error": None}


class MockTable:
    """Mock table for development without Supabase."""

    def __init__(self, name: str):
        self.name = name
        self._data = []

    def select(self, *args, **kwargs):
        return self

    def insert(self, data):
        self._data.append(data)
        return self

    def update(self, data):
        return self

    def delete(self):
        return self

    def eq(self, column, value):
        return self

    def single(self):
        return self

    def execute(self):
        """Execute the query and return mock data."""
        return {"data": None, "error": None}
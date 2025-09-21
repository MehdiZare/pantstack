import asyncio
from services.auth.app.api.main import healthz


def test_healthz():
    """Test health check endpoint."""
    result = asyncio.run(healthz())
    assert result["status"] == "ok"
    assert result["service"] == "auth"

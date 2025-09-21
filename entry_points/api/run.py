"""Run script for the API server."""

import os

import uvicorn


def main():
    """Run the API server."""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"

    if workers > 1:
        # Multi-worker mode (production)
        uvicorn.run(
            "entry_points.api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info",
        )
    else:
        # Single worker mode (development)
        uvicorn.run(
            "entry_points.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="debug" if reload else "info",
        )


if __name__ == "__main__":
    main()
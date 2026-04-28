"""Info Retrieval Agent — Application entry point."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main() -> None:
    """Start the FastAPI application server."""
    # Validate configuration before starting
    try:
        from src.config.settings import get_settings

        get_settings()
    except Exception as e:
        logging.error("Configuration error: %s", e)
        sys.exit(1)

    import uvicorn

    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()

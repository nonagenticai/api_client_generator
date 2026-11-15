"""
ingestion_service client singleton.

Auto-configured from environment variables.
"""

import os
from typing import Optional

from .client import IngestionServiceClient

_CLIENT_INSTANCE: Optional[IngestionServiceClient] = None


def get_client() -> IngestionServiceClient:
    """
    Get or create the ingestion_service client instance.

    Auto-configures from environment variables:
    - INGESTION_SERVICE_URL: Base URL for the API
    - INGESTION_SERVICE_TOKEN: Authentication token

    Returns:
        Configured IngestionServiceClient instance
    """
    global _CLIENT_INSTANCE

    if _CLIENT_INSTANCE is None:
        base_url = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8000")
        auth_token = os.getenv("INGESTION_SERVICE_TOKEN")

        if not base_url:
            raise ValueError("INGESTION_SERVICE_URL environment variable is required")

        _CLIENT_INSTANCE = IngestionServiceClient(
            base_url=base_url,
            auth_token=auth_token,
        )

    return _CLIENT_INSTANCE


def reset_client() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _CLIENT_INSTANCE
    _CLIENT_INSTANCE = None

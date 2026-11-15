"""Cleanup strategies for API validation testing."""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class CleanupStrategy(str, Enum):
    """Strategy for cleaning up test data."""

    TRANSACTION = "transaction"  # Use DB transactions (requires DB support)
    TRACK_AND_DELETE = "track_and_delete"  # Track resources and delete them
    TEST_DATABASE = "test_database"  # Use separate test DB, wipe after
    SNAPSHOT_RESTORE = "snapshot_restore"  # Create DB snapshot, restore after
    NONE = "none"  # No cleanup (dangerous!)


@dataclass
class CreatedResource:
    """Represents a resource created during testing."""

    endpoint: str  # e.g., "/api/users"
    method: str  # e.g., "POST"
    resource_id: Optional[str] = None  # Extracted ID
    location_url: Optional[str] = None  # From Location header
    delete_endpoint: Optional[str] = None  # How to delete it
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceTracker:
    """
    Tracks resources created during API testing for cleanup.

    Usage:
        tracker = ResourceTracker()

        # Automatically track POST/PUT responses
        async with httpx.AsyncClient() as client:
            response = await client.post("/api/users", json={...})
            tracker.track_response(response, endpoint="/api/users", method="POST")

        # Cleanup all created resources
        await tracker.cleanup_all(client)
    """

    def __init__(self) -> None:
        self.created_resources: List[CreatedResource] = []
        self.id_extractors: Dict[str, Callable[..., Any]] = {}
        self.delete_patterns: Dict[str, str] = {}

    def register_id_extractor(self, endpoint_pattern: str, extractor: Callable[..., Any]) -> None:
        """
        Register custom ID extractor for an endpoint.

        Args:
            endpoint_pattern: Regex pattern or exact endpoint
            extractor: Function that takes response JSON and returns resource ID

        Example:
            tracker.register_id_extractor(
                "/api/users",
                lambda data: data.get("id") or data.get("user_id")
            )
        """
        self.id_extractors[endpoint_pattern] = extractor

    def register_delete_pattern(self, create_endpoint: str, delete_pattern: str) -> None:
        """
        Register how to delete resources from an endpoint.

        Args:
            create_endpoint: Creation endpoint (e.g., "/api/users")
            delete_pattern: Delete pattern with {id} placeholder (e.g., "/api/users/{id}")

        Example:
            tracker.register_delete_pattern("/api/users", "/api/users/{id}")
        """
        self.delete_patterns[create_endpoint] = delete_pattern

    def track_response(
        self,
        response: httpx.Response,
        endpoint: str,
        method: str,
    ) -> Optional[CreatedResource]:
        """
        Track a response for potential cleanup.

        Automatically extracts resource IDs from:
        - Response JSON (common ID fields)
        - Location header
        - Custom extractors
        """
        if method.upper() not in ["POST", "PUT", "PATCH"]:
            return None

        if response.status_code not in [200, 201, 202, 204]:
            return None

        resource = CreatedResource(endpoint=endpoint, method=method)

        # Extract from Location header
        location = response.headers.get("Location")
        if location:
            resource.location_url = location
            # Try to extract ID from URL
            parts = location.rstrip("/").split("/")
            if parts:
                potential_id = parts[-1]
                if potential_id and not potential_id.startswith("?"):
                    resource.resource_id = potential_id

        # Extract from response body
        try:
            data = response.json()

            # Try custom extractor first
            if endpoint in self.id_extractors:
                resource_id = self.id_extractors[endpoint](data)
                if resource_id:
                    resource.resource_id = str(resource_id)

            # Try common ID fields
            if not resource.resource_id:
                for id_field in ["id", "uuid", "resourceId", "resource_id", "_id"]:
                    if id_field in data:
                        resource.resource_id = str(data[id_field])
                        break

            resource.metadata = data
        except Exception as e:
            logger.debug(f"Could not extract ID from response: {e}")

        # Determine delete endpoint
        if endpoint in self.delete_patterns and resource.resource_id:
            resource.delete_endpoint = self.delete_patterns[endpoint].format(
                id=resource.resource_id
            )
        elif resource.location_url:
            resource.delete_endpoint = resource.location_url

        if resource.resource_id or resource.location_url:
            self.created_resources.append(resource)
            logger.info(f"Tracked resource: {method} {endpoint} -> ID={resource.resource_id}")
            return resource

        return None

    async def cleanup_all(
        self,
        client: httpx.AsyncClient,
        auth_header: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Cleanup all tracked resources in reverse order.

        Args:
            client: HTTP client to use for cleanup
            auth_header: Optional auth headers to include

        Returns:
            Summary of cleanup results
        """
        results: Dict[str, Any] = {
            "total": len(self.created_resources),
            "deleted": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        # Cleanup in reverse order (last created, first deleted)
        for resource in reversed(self.created_resources):
            if not resource.delete_endpoint:
                logger.warning(
                    f"No delete endpoint for {resource.method} {resource.endpoint}, skipping"
                )
                results["skipped"] += 1
                continue

            try:
                headers = auth_header or {}
                response = await client.delete(resource.delete_endpoint, headers=headers)

                if response.status_code in [200, 204, 404]:
                    # 404 is OK - resource already gone
                    results["deleted"] += 1
                    logger.info(f"Deleted: {resource.delete_endpoint}")
                else:
                    results["failed"] += 1
                    error_msg = (
                        f"Failed to delete {resource.delete_endpoint}: {response.status_code}"
                    )
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Error deleting {resource.delete_endpoint}: {e}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        self.created_resources.clear()
        return results


class TransactionCleanup:
    """
    Database transaction-based cleanup for Postgres/MySQL.

    Requires API to support transactional testing mode.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self._transaction_id: Optional[str] = None

    async def begin_transaction(self, client: httpx.AsyncClient) -> None:
        """Start a test transaction (requires API support)."""
        # This requires the API to expose a test-only endpoint
        # Example: POST /api/_test/begin_transaction
        response = await client.post(
            "/api/_test/begin_transaction",
            json={"isolation_level": "READ_COMMITTED"},
        )
        response.raise_for_status()
        self._transaction_id = response.json()["transaction_id"]
        logger.info(f"Started transaction: {self._transaction_id}")

    async def rollback_transaction(self, client: httpx.AsyncClient) -> None:
        """Rollback the test transaction."""
        if not self._transaction_id:
            return

        await client.post(
            "/api/_test/rollback_transaction",
            json={"transaction_id": self._transaction_id},
        )
        logger.info(f"Rolled back transaction: {self._transaction_id}")
        self._transaction_id = None


class SnapshotCleanup:
    """
    Database snapshot-based cleanup.

    Creates snapshot before testing, restores after.
    """

    def __init__(self, db_url: str, snapshot_name: str = "api_test_snapshot"):
        self.db_url = db_url
        self.snapshot_name = snapshot_name

    async def create_snapshot(self) -> None:
        """Create database snapshot (implementation depends on DB type)."""
        # For Postgres: pg_dump
        # For MySQL: mysqldump
        # For SQLite: file copy
        logger.info(f"Creating snapshot: {self.snapshot_name}")
        # Implementation would go here

    async def restore_snapshot(self) -> None:
        """Restore database from snapshot."""
        logger.info(f"Restoring snapshot: {self.snapshot_name}")
        # Implementation would go here

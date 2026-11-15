"""
ingestion_service API client.

Auto-generated async HTTP client from OpenAPI specification.
DO NOT EDIT - regenerate using apigen.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from .models import *

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        detail: Optional[Any] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class NotFoundError(APIError):
    """Resource not found (404)."""

    pass


class RequestValidationError(APIError):
    """Validation error (422)."""

    pass


class AuthenticationError(APIError):
    """Authentication error (401)."""

    pass


class IngestionServiceClient:
    """
    Async HTTP client for Ingestion Microservice.

    Document parsing and preprocessing service for Knowledge Augmented Graph
    """

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        retries: int = 3,
        verify_ssl: bool = True,
    ):
        """
        Initialize the client.

        Args:
            base_url: Base URL for the API
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
            retries: Number of retries for failed requests
            verify_ssl: Whether to verify SSL certificates (set to False for self-signed certs)
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self.retries = retries
        self.verify_ssl = verify_ssl

        # HTTP client will be created on first use
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "IngestionServiceClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = {}

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        """
        Make an HTTP request.

        Args:
            method: HTTP method
            path: Request path
            params: Query parameters
            json: JSON body

        Returns:
            Response data (parsed)

        Raises:
            APIError: On HTTP errors
        """
        await self._ensure_client()

        url = path
        logger.info(f"{method} {url}", extra={"params": params})

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
            )

            # Handle errors
            if response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {url}",
                    status_code=404,
                )
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    status_code=401,
                )
            elif response.status_code == 422:
                raise RequestValidationError(
                    "Validation failed",
                    status_code=422,
                    detail=response.json() if response.content else None,
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"HTTP {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            # Parse response
            if response.status_code == 204 or not response.content:
                return None

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise APIError(f"HTTP error: {e}") from e

    async def health_check_health_get(
        self,
    ) -> HealthResponse:
        """
                Health Check

                Basic health check endpoint
        Returns 200 if service is operational


                Returns:
                    HealthResponse
        """
        # Build path with path parameters
        path = "/health"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return HealthResponse.model_validate(response_data)

    async def detailed_health_check_health_detailed_get(
        self,
    ) -> DetailedHealthResponse:
        """
        Detailed Health Check

        Detailed health check with component and system status


        Returns:
            DetailedHealthResponse
        """
        # Build path with path parameters
        path = "/health/detailed"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return DetailedHealthResponse.model_validate(response_data)

    async def readiness_check_health_ready_get(
        self,
    ) -> str:
        """
                Readiness Check

                Readiness probe for Kubernetes
        Returns 200 only if service is ready to accept traffic


                Returns:
                    str
        """
        # Build path with path parameters
        path = "/health/ready"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def liveness_check_health_live_get(
        self,
    ) -> str:
        """
                Liveness Check

                Liveness probe for Kubernetes
        Returns 200 if service process is alive


                Returns:
                    str
        """
        # Build path with path parameters
        path = "/health/live"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def ingest_document_ingest_post(
        self,
        data: BodyIngestDocumentIngestPost,
    ) -> Dict[str, Any]:
        """
                Ingest Document

                Upload and parse a document

        Supported formats: PDF, EPUB, MOBI, AZW, DOCX, ODT, RTF, Markdown, TXT, HTML

        Args:
            file: Document file to upload
            send_to_kag: If True, send parsed document to KAG for ingestion (default: True).
                         If False, only parse and return the document without KAG ingestion.

        Returns:
            {
                "job_id": "uuid",
                "status": "processing",
                "message": "Document uploaded successfully",
                "send_to_kag": true/false
            }


                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/ingest"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return response_data

    async def ingest_document_sync_ingest_sync_post(
        self,
        data: BodyIngestDocumentSyncIngestSyncPost,
    ) -> str:
        """
                Ingest Document Sync

                Upload and parse a document synchronously (blocks until complete)

        Supported formats: PDF, EPUB, MOBI, AZW, DOCX, ODT, RTF, Markdown, TXT, HTML

        Args:
            file: Document file to upload
            send_to_kag: If True, send parsed document to KAG for ingestion (default: True).
                         If False, only parse and return the document without KAG ingestion.

        Returns:
            ParsedDocument with full parsing results (if send_to_kag=False)
            OR
            Dict with job_id and KAG ingestion status (if send_to_kag=True)


                Returns:
                    str
        """
        # Build path with path parameters
        path = "/ingest/sync"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return response_data

    async def get_job_status_jobs__job_id__get(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """
                Get Job Status

                Get the status of a processing job

        Returns:
            {
                "job_id": "uuid",
                "status": "processing|completed|failed",
                "filename": "original_filename.pdf",
                "result": ParsedDocument | null,
                "error": str | null
            }

                Args:
                    job_id: job_id

                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/jobs/{job_id}"
        path = path.replace("{" + "job_id" + "}", str(job_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def delete_job_jobs__job_id__delete(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """
                Delete Job

                Delete a job from the in-memory store

        Returns:
            {"message": "Job deleted successfully"}

                Args:
                    job_id: job_id

                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/jobs/{job_id}"
        path = path.replace("{" + "job_id" + "}", str(job_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="DELETE",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def list_jobs_jobs_get(
        self,
    ) -> Dict[str, Any]:
        """
                List Jobs

                List all jobs (for debugging/monitoring)

        Returns:
            {
                "total_jobs": int,
                "jobs": [
                    {
                        "job_id": "uuid",
                        "status": "processing|completed|failed",
                        "filename": "file.pdf"
                    },
                    ...
                ]
            }


                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/jobs"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def clear_all_jobs_jobs_clear_post(
        self,
    ) -> Dict[str, Any]:
        """
                Clear All Jobs

                Clear all jobs from memory (for cleanup/debugging)

        Returns:
            {"message": "All jobs cleared", "count": int}


                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/jobs/clear"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def get_supported_formats_formats_get(
        self,
    ) -> SupportedFormatsResponse:
        """
                Get Supported Formats

                Get list of all supported document formats.

        Returns:
            List of supported formats with metadata

        Example Response:
            ```json
            {
                "formats": [
                    {
                        "format": "pdf",
                        "extensions": [".pdf"],
                        "mime_types": ["application/pdf"],
                        "description": "Portable Document Format",
                        "parsers": ["EnhancedPDFParser", "DoclingAdapter", "PyPDFAdapter"]
                    },
                    ...
                ],
                "total_count": 15
            }
            ```


                Returns:
                    SupportedFormatsResponse
        """
        # Build path with path parameters
        path = "/formats"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return SupportedFormatsResponse.model_validate(response_data)

    async def detect_format_formats_detect_post(
        self,
        data: BodyDetectFormatFormatsDetectPost,
    ) -> FormatDetectionResponse:
        """
                Detect Format

                Detect the format of an uploaded file.

        Does not process or store the file, only detects its format.

        Args:
            file: Uploaded file

        Returns:
            Format detection results

        Example Response:
            ```json
            {
                "filename": "document.pdf",
                "detected_format": "pdf",
                "confidence": 0.95,
                "mime_type": "application/pdf",
                "supported": true
            }
            ```


                Returns:
                    FormatDetectionResponse
        """
        # Build path with path parameters
        path = "/formats/detect"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return FormatDetectionResponse.model_validate(response_data)

    async def check_format_supported_formats_supported__format_name__get(
        self,
        format_name: str,
    ) -> Dict[str, Any]:
        """
                Check Format Supported

                Check if a specific format is supported.

        Args:
            format_name: Format name to check (e.g., 'pdf', 'epub')

        Returns:
            Dictionary with supported status

        Example Response:
            ```json
            {
                "supported": true
            }
            ```

                Args:
                    format_name: format_name

                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/formats/supported/{format_name}"
        path = path.replace("{" + "format_name" + "}", str(format_name))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def batch_upload_batch_upload_post(
        self,
        data: BodyBatchUploadBatchUploadPost,
        async_processing: bool = None,
    ) -> BatchUploadResponse:
        """
                Batch Upload

                Upload and process multiple documents in batch.

        Accepts multiple files and processes them asynchronously using Celery workers.

        Args:
            files: List of files to upload
            async_processing: Whether to process asynchronously (default: True)

        Returns:
            Batch upload response with job IDs

        Example Response:
            ```json
            {
                "success": true,
                "total_files": 5,
                "accepted": [
                    {"filename": "doc1.pdf", "job_id": "job-123"},
                    {"filename": "doc2.epub", "job_id": "job-124"}
                ],
                "rejected": [
                    {"filename": "doc3.xyz", "reason": "Unsupported format"}
                ],
                "batch_id": "batch-abc"
            }
            ```

                Args:
                    async_processing: async_processing
                    data: Request body data
                Returns:
                    BatchUploadResponse
        """
        # Build path with path parameters
        path = "/batch/upload"

        # Build query parameters
        params = {}
        if async_processing is not None:
            params["async_processing"] = async_processing

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return BatchUploadResponse.model_validate(response_data)

    async def get_batch_status_batch__batch_id__status_get(
        self,
        batch_id: str,
    ) -> BatchStatusResponse:
        """
                Get Batch Status

                Get status of a batch upload.

        Args:
            batch_id: Batch ID to query

        Returns:
            Batch status with job details

        Example Response:
            ```json
            {
                "batch_id": "batch-abc",
                "total_jobs": 5,
                "completed": 3,
                "processing": 1,
                "queued": 0,
                "failed": 1,
                "jobs": [...]
            }
            ```

                Args:
                    batch_id: batch_id

                Returns:
                    BatchStatusResponse
        """
        # Build path with path parameters
        path = "/batch/{batch_id}/status"
        path = path.replace("{" + "batch_id" + "}", str(batch_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return BatchStatusResponse.model_validate(response_data)

    async def retry_failed_jobs_batch__batch_id__retry_failed_post(
        self,
        batch_id: str,
    ) -> Dict[str, Any]:
        """
                Retry Failed Jobs

                Retry all failed jobs in a batch.

        Args:
            batch_id: Batch ID to retry

        Returns:
            Dictionary with retry results

                Args:
                    batch_id: batch_id

                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/batch/{batch_id}/retry-failed"
        path = path.replace("{" + "batch_id" + "}", str(batch_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def scrape_url_scrape_url_post(
        self,
        data: ScrapeURLRequest,
    ) -> ScrapeResponse:
        """
                Scrape Url

                Scrape a single URL.

        Supports both synchronous (Playwright) and asynchronous (background task) scraping.

        Args:
            request: Scraping configuration
            background_tasks: FastAPI background tasks

        Returns:
            Scraping result or job ID


                Returns:
                    ScrapeResponse
        """
        # Build path with path parameters
        path = "/scrape/url"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return ScrapeResponse.model_validate(response_data)

    async def scrape_bulk_scrape_bulk_post(
        self,
        data: ScrapeBulkRequest,
    ) -> ScrapeResponse:
        """
                Scrape Bulk

                Scrape multiple URLs efficiently.

        Uses Scrapy for concurrent scraping with rate limiting.

        Args:
            request: Bulk scraping configuration
            background_tasks: FastAPI background tasks

        Returns:
            Scraping session ID


                Returns:
                    ScrapeResponse
        """
        # Build path with path parameters
        path = "/scrape/bulk"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return ScrapeResponse.model_validate(response_data)

    async def scrape_sitemap_scrape_sitemap_post(
        self,
        data: ScrapeSitemapRequest,
    ) -> ScrapeResponse:
        """
                Scrape Sitemap

                Scrape URLs from an XML sitemap.

        Parses the sitemap and queues all discovered URLs for scraping.

        Args:
            request: Sitemap scraping configuration
            background_tasks: FastAPI background tasks

        Returns:
            Scraping session ID


                Returns:
                    ScrapeResponse
        """
        # Build path with path parameters
        path = "/scrape/sitemap"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
            json=data.model_dump(by_alias=True) if hasattr(data, "model_dump") else data,
        )

        # Parse and validate response
        return ScrapeResponse.model_validate(response_data)

    async def list_sessions_scrape_sessions_get(
        self,
        status: Union[str, Any] = None,
        limit: int = None,
    ) -> Dict[str, Any]:
        """
                List Sessions

                List scraping sessions.

        Args:
            status: Optional status filter (queued, running, completed, failed)
            limit: Maximum number of sessions to return

        Returns:
            List of scraping sessions

                Args:
                    status: Filter by status
                    limit: Maximum number of sessions to return

                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/scrape/sessions"

        # Build query parameters
        params = {}
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = limit

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def get_session_scrape_sessions__session_id__get(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
                Get Session

                Get details of a scraping session.

        Args:
            session_id: Scraping session ID

        Returns:
            Session details

                Args:
                    session_id: session_id

                Returns:
                    Dict[str, Any]
        """
        # Build path with path parameters
        path = "/scrape/sessions/{session_id}"
        path = path.replace("{" + "session_id" + "}", str(session_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

    async def cancel_session_scrape_sessions__session_id__delete(
        self,
        session_id: str,
    ) -> ScrapeResponse:
        """
                Cancel Session

                Cancel a scraping session.

        Args:
            session_id: Scraping session ID

        Returns:
            Success response

                Args:
                    session_id: session_id

                Returns:
                    ScrapeResponse
        """
        # Build path with path parameters
        path = "/scrape/sessions/{session_id}"
        path = path.replace("{" + "session_id" + "}", str(session_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="DELETE",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return ScrapeResponse.model_validate(response_data)

    async def pause_session_scrape_sessions__session_id__pause_post(
        self,
        session_id: str,
    ) -> ScrapeResponse:
        """
                Pause Session

                Pause a running scraping session.

        Args:
            session_id: Scraping session ID

        Returns:
            Success response

                Args:
                    session_id: session_id

                Returns:
                    ScrapeResponse
        """
        # Build path with path parameters
        path = "/scrape/sessions/{session_id}/pause"
        path = path.replace("{" + "session_id" + "}", str(session_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return ScrapeResponse.model_validate(response_data)

    async def resume_session_scrape_sessions__session_id__resume_post(
        self,
        session_id: str,
    ) -> ScrapeResponse:
        """
                Resume Session

                Resume a paused scraping session.

        Args:
            session_id: Scraping session ID
            background_tasks: FastAPI background tasks

        Returns:
            Success response

                Args:
                    session_id: session_id

                Returns:
                    ScrapeResponse
        """
        # Build path with path parameters
        path = "/scrape/sessions/{session_id}/resume"
        path = path.replace("{" + "session_id" + "}", str(session_id))

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="POST",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return ScrapeResponse.model_validate(response_data)

    async def root__get(
        self,
    ) -> str:
        """
        Root

        Root endpoint with service information


        Returns:
            str
        """
        # Build path with path parameters
        path = "/"

        # Build query parameters
        params = {}

        # Build headers
        headers = {}

        # Make request
        response_data = await self._request(
            method="GET",
            path=path,
            params=params if params else None,
        )

        # Parse and validate response
        return response_data

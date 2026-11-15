"""
ingestion_service API models.

Auto-generated Pydantic v2 models from OpenAPI specification.
DO NOT EDIT - regenerate using apigen.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Union

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class BatchStatusResponse(BaseModel):
    """Response model for batch status."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    batch_id: str = Field(
        ...,
    )
    total_jobs: int = Field(
        ...,
    )
    completed: int = Field(
        ...,
    )
    processing: int = Field(
        ...,
    )
    queued: int = Field(
        ...,
    )
    failed: int = Field(
        ...,
    )
    jobs: List[Dict[str, Any]] = Field(
        ...,
    )


class BatchUploadResponse(BaseModel):
    """Response model for batch upload."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    success: bool = Field(
        ...,
    )
    total_files: int = Field(
        ...,
    )
    accepted: List[Dict[str, Any]] = Field(
        ...,
    )
    rejected: List[Dict[str, Any]] = Field(
        ...,
    )
    batch_id: str = Field(
        ...,
    )


class BodyBatchUploadBatchUploadPost(BaseModel):
    """BodyBatchUploadBatchUploadPost model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    files: List[bytes] = Field(
        ...,
        description="Multiple files to upload",
    )


class BodyDetectFormatFormatsDetectPost(BaseModel):
    """BodyDetectFormatFormatsDetectPost model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    file: bytes = Field(
        ...,
        description="File to detect format",
    )


class BodyIngestDocumentIngestPost(BaseModel):
    """BodyIngestDocumentIngestPost model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    file: bytes = Field(
        ...,
    )
    send_to_kag: bool = None


class BodyIngestDocumentSyncIngestSyncPost(BaseModel):
    """BodyIngestDocumentSyncIngestSyncPost model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    file: bytes = Field(
        ...,
    )
    send_to_kag: bool = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check with component status"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    status: str = Field(
        ...,
    )
    timestamp: datetime = Field(
        ...,
    )
    service: str = Field(
        ...,
    )
    version: str = Field(
        ...,
    )
    components: Dict[str, Any] = Field(
        ...,
    )
    system: Dict[str, Any] = Field(
        ...,
    )


class FormatDetectionResponse(BaseModel):
    """Response model for format detection."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    filename: str = Field(
        ...,
    )
    detected_format: str = Field(
        ...,
    )
    confidence: float = Field(
        ...,
    )
    mime_type: Union[str, Any] = None
    supported: bool = Field(
        ...,
    )


class HTTPValidationError(BaseModel):
    """HTTPValidationError model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    detail: List[ValidationError] = None


class HealthResponse(BaseModel):
    """Basic health check response"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    status: str = Field(
        ...,
    )
    timestamp: datetime = Field(
        ...,
    )
    service: str = Field(
        ...,
    )
    version: str = Field(
        ...,
    )


class ScrapeBulkRequest(BaseModel):
    """Request model for scraping multiple URLs"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    urls: List[AnyUrl] = Field(
        ...,
    )
    scraper_type: Union[ScraperType, Any] = None
    delay: Union[float, Any] = Field(
        default=None,
        description="Delay between requests (seconds)",
    )
    timeout: Union[float, Any] = Field(
        default=None,
        description="Request timeout (seconds)",
    )
    follow_links: Union[bool, Any] = Field(
        default=None,
        description="Follow links",
    )
    max_depth: Union[int, Any] = Field(
        default=None,
        description="Maximum depth for link following",
    )
    respect_robots_txt: Union[bool, Any] = Field(
        default=None,
        description="Respect robots.txt",
    )
    allowed_domains: Union[List[str], Any] = Field(
        default=None,
        description="Allowed domains for crawling",
    )
    max_pages: Union[int, Any] = Field(
        default=None,
        description="Maximum number of pages to scrape",
    )
    credential_id: Union[str, Any] = Field(
        default=None,
        description="URL credential ID from Secrets API",
    )


class ScrapeResponse(BaseModel):
    """Response model for scraping operations"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    success: bool = Field(
        ...,
    )
    message: str = Field(
        ...,
    )
    session_id: Union[str, Any] = None
    result: Union[Dict[str, Any], Any] = None


class ScrapeSitemapRequest(BaseModel):
    """Request model for scraping from a sitemap"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    sitemap_url: AnyUrl = Field(
        ...,
        min_length=1,
        max_length=2083,
    )
    max_urls: Union[int, Any] = Field(
        default=None,
        description="Maximum URLs to scrape from sitemap",
    )
    delay: Union[float, Any] = Field(
        default=None,
        description="Delay between requests (seconds)",
    )
    timeout: Union[float, Any] = Field(
        default=None,
        description="Request timeout (seconds)",
    )
    respect_robots_txt: Union[bool, Any] = Field(
        default=None,
        description="Respect robots.txt",
    )
    allowed_domains: Union[List[str], Any] = Field(
        default=None,
        description="Allowed domains",
    )
    credential_id: Union[str, Any] = Field(
        default=None,
        description="URL credential ID from Secrets API",
    )


class ScrapeURLRequest(BaseModel):
    """Request model for scraping a single URL"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    url: AnyUrl = Field(
        ...,
        min_length=1,
        max_length=2083,
    )
    scraper_type: Union[ScraperType, Any] = None
    delay: Union[float, Any] = Field(
        default=None,
        description="Delay between requests (seconds)",
    )
    timeout: Union[float, Any] = Field(
        default=None,
        description="Request timeout (seconds)",
    )
    screenshot: Union[bool, Any] = Field(
        default=None,
        description="Capture screenshot",
    )
    follow_links: Union[bool, Any] = Field(
        default=None,
        description="Follow links on page",
    )
    max_depth: Union[int, Any] = Field(
        default=None,
        description="Maximum depth for link following",
    )
    respect_robots_txt: Union[bool, Any] = Field(
        default=None,
        description="Respect robots.txt",
    )
    user_agent: Union[str, Any] = Field(
        default=None,
        description="Custom user agent",
    )
    credential_id: Union[str, Any] = Field(
        default=None,
        description="URL credential ID from Secrets API",
    )


class ScraperType(str, Enum):
    """Type of scraper to use"""

    PLAYWRIGHT = "playwright"
    SCRAPY = "scrapy"
    SIMPLE = "simple"


class SupportedFormatsResponse(BaseModel):
    """Response model for supported formats."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    formats: List[Dict[str, Any]] = Field(
        ...,
    )
    total_count: int = Field(
        ...,
    )


class ValidationError(BaseModel):
    """ValidationError model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    loc: List[Union[str, int]] = Field(
        ...,
    )
    msg: str = Field(
        ...,
    )
    type_: str = Field(
        ...,
        alias="type",
    )

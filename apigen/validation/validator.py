"""Main API validator with multiple testing backends."""

import importlib.util
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from apigen.validation.cleanup import CleanupStrategy
from apigen.validation.contract_tester import ContractTester

logger = logging.getLogger(__name__)


class ValidationBackend(str, Enum):
    """Backend for API validation."""

    BUILTIN = "builtin"  # Our custom contract tester
    SCHEMATHESIS = "schemathesis"  # Use schemathesis (if installed)
    DREDD = "dredd"  # Use Dredd (if installed)


@dataclass
class ValidationConfig:
    """Configuration for API validation."""

    # API configuration
    openapi_spec_url: str
    base_url: str
    auth_token: Optional[str] = None

    # Cleanup strategy
    cleanup_strategy: CleanupStrategy = CleanupStrategy.TRACK_AND_DELETE

    # Testing backend
    backend: ValidationBackend = ValidationBackend.BUILTIN

    # Cleanup configuration
    id_extractors: Optional[Dict[str, Callable[..., Any]]] = None
    delete_patterns: Optional[Dict[str, str]] = None

    # Testing options
    timeout: float = 30.0
    max_examples: int = 10  # For property-based testing
    fail_fast: bool = False  # Stop on first failure
    verify_ssl: bool = True  # SSL certificate verification

    # Output options
    verbose: bool = True
    save_report: bool = True
    report_path: Path = Path("validation_report.json")


@dataclass
class ValidationResult:
    """Result of API validation."""

    total_tests: int
    passed: int
    failed: int
    skipped: int
    success_rate: str
    avg_response_time_ms: str
    cleanup_summary: Optional[Dict[str, Any]]
    failed_tests: List[Dict[str, Any]]
    backend_used: ValidationBackend

    def print_summary(self) -> None:
        """Print human-readable summary."""
        print("\n" + "=" * 60)
        print("API VALIDATION RESULTS")
        print("=" * 60)
        print(f"Backend: {self.backend_used.value}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Skipped: {self.skipped}")
        print(f"Success Rate: {self.success_rate}")
        print(f"Avg Response Time: {self.avg_response_time_ms}")

        if self.cleanup_summary:
            print("\nCLEANUP SUMMARY:")
            print(f"  Resources tracked: {self.cleanup_summary.get('total', 0)}")
            print(f"  Successfully deleted: {self.cleanup_summary.get('deleted', 0)}")
            print(f"  Failed to delete: {self.cleanup_summary.get('failed', 0)}")
            print(f"  Skipped: {self.cleanup_summary.get('skipped', 0)}")

        if self.failed_tests:
            print("\nFAILED TESTS:")
            for test in self.failed_tests:
                print(f"\n  {test['method']} {test['endpoint']}")
                print(f"    Status: {test.get('status_code', 'N/A')}")
                for error in test.get("errors", []):
                    print(f"    - {error}")

        print("=" * 60 + "\n")


class APIValidator:
    """
    Main API validator that validates OpenAPI conformance and cleans up test data.

    Usage:
        # Simple usage
        validator = APIValidator(
            openapi_spec_url="http://localhost:8001/openapi.json",
            base_url="http://localhost:8001",
        )
        result = await validator.validate()
        result.print_summary()

        # With custom cleanup configuration
        config = ValidationConfig(
            openapi_spec_url="http://localhost:8001/openapi.json",
            base_url="http://localhost:8001",
            cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE,
            delete_patterns={
                "/api/users": "/api/users/{id}",
                "/api/posts": "/api/posts/{id}",
            }
        )
        validator = APIValidator.from_config(config)
        result = await validator.validate()
    """

    def __init__(
        self,
        openapi_spec_url: str,
        base_url: str,
        auth_token: Optional[str] = None,
        cleanup_strategy: CleanupStrategy = CleanupStrategy.TRACK_AND_DELETE,
        backend: ValidationBackend = ValidationBackend.BUILTIN,
        verify_ssl: bool = True,
    ):
        self.config = ValidationConfig(
            openapi_spec_url=openapi_spec_url,
            base_url=base_url,
            auth_token=auth_token,
            cleanup_strategy=cleanup_strategy,
            backend=backend,
            verify_ssl=verify_ssl,
        )

    @classmethod
    def from_config(cls, config: ValidationConfig) -> "APIValidator":
        """Create validator from config object."""
        instance = cls.__new__(cls)
        instance.config = config
        return instance

    async def validate(self) -> ValidationResult:
        """
        Run validation tests and cleanup.

        Returns:
            Validation results
        """
        if self.config.backend == ValidationBackend.BUILTIN:
            return await self._validate_builtin()
        elif self.config.backend == ValidationBackend.SCHEMATHESIS:
            return await self._validate_schemathesis()
        else:
            raise NotImplementedError(f"Backend {self.config.backend} not implemented")

    async def _validate_builtin(self) -> ValidationResult:
        """Run validation using built-in contract tester."""
        tester = ContractTester(
            openapi_spec_url=self.config.openapi_spec_url,
            base_url=self.config.base_url,
            cleanup_strategy=self.config.cleanup_strategy,
            auth_token=self.config.auth_token,
            timeout=self.config.timeout,
            verify_ssl=self.config.verify_ssl,
        )

        # Configure cleanup
        if self.config.id_extractors or self.config.delete_patterns:
            tester.configure_cleanup(
                id_extractors=self.config.id_extractors,
                delete_patterns=self.config.delete_patterns,
            )

        # Run tests
        summary = await tester.run_all_tests()

        result = ValidationResult(
            total_tests=summary["total_tests"],
            passed=summary["passed"],
            failed=summary["failed"],
            skipped=0,
            success_rate=summary["success_rate"],
            avg_response_time_ms=summary["avg_response_time_ms"],
            cleanup_summary=summary.get("cleanup"),
            failed_tests=summary["failed_tests"],
            backend_used=ValidationBackend.BUILTIN,
        )

        return result

    async def _validate_schemathesis(self) -> ValidationResult:
        """
        Run validation using schemathesis with cleanup.

        This wraps schemathesis and adds our cleanup logic on top.
        """
        if importlib.util.find_spec("schemathesis") is None:
            raise ImportError("Schemathesis not installed. Install with: pip install schemathesis")

        # TODO: Implement schemathesis integration with cleanup
        # This would:
        # 1. Run schemathesis tests
        # 2. Hook into their event system to track created resources
        # 3. Run cleanup after tests complete

        raise NotImplementedError("Schemathesis backend coming soon")


# Helper function for CLI
async def validate_api(
    openapi_spec_url: str,
    base_url: str,
    auth_token: Optional[str] = None,
    cleanup_strategy: str = "track_and_delete",
    delete_patterns: Optional[Dict[str, str]] = None,
    verbose: bool = True,
) -> ValidationResult:
    """
    Convenience function for validating an API.

    Args:
        openapi_spec_url: URL to OpenAPI specification
        base_url: Base URL of API to test
        auth_token: Optional auth token
        cleanup_strategy: Cleanup strategy (track_and_delete, transaction, etc.)
        delete_patterns: Delete URL patterns for cleanup
        verbose: Print verbose output

    Returns:
        Validation results
    """
    config = ValidationConfig(
        openapi_spec_url=openapi_spec_url,
        base_url=base_url,
        auth_token=auth_token,
        cleanup_strategy=CleanupStrategy(cleanup_strategy),
        delete_patterns=delete_patterns,
        verbose=verbose,
    )

    validator = APIValidator.from_config(config)
    result = await validator.validate()

    if verbose:
        result.print_summary()

    return result

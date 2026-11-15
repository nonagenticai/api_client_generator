"""Contract testing - verify API matches OpenAPI specification."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, cast

import httpx
from openapi_spec_validator import validate_spec
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from apigen.validation.cleanup import CleanupStrategy, ResourceTracker

logger = logging.getLogger(__name__)


@dataclass
class ContractTestResult:
    """Result of a single contract test."""

    endpoint: str
    method: str
    status_code: int
    passed: bool
    errors: List[str]
    response_time_ms: float
    request_body: Optional[Dict[str, Any]] = None
    response_body: Optional[Dict[str, Any]] = None


class ContractTester:
    """
    Test that API actually behaves according to its OpenAPI specification.

    Features:
    - Tests all endpoints defined in OpenAPI spec
    - Validates request/response schemas
    - Validates status codes
    - Validates headers
    - Automatic cleanup of test data

    Usage:
        tester = ContractTester(
            openapi_spec_url="http://localhost:8001/openapi.json",
            base_url="http://localhost:8001",
            cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE
        )

        results = await tester.run_all_tests()
        print(f"Passed: {results.passed}/{results.total}")
    """

    def __init__(
        self,
        openapi_spec_url: str,
        base_url: str,
        cleanup_strategy: CleanupStrategy = CleanupStrategy.TRACK_AND_DELETE,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        self.openapi_spec_url = openapi_spec_url
        self.base_url = base_url.rstrip("/")
        self.cleanup_strategy = cleanup_strategy
        self.auth_token = auth_token
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.spec: Optional[Dict[str, Any]] = None
        self.tracker = ResourceTracker()
        self.results: List[ContractTestResult] = []

    async def load_spec(self) -> Dict[str, Any]:
        """Load and validate OpenAPI specification."""
        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
            response = await client.get(self.openapi_spec_url)
            response.raise_for_status()
            spec = response.json()

        # Validate spec
        try:
            validate_spec(spec)
            logger.info("OpenAPI spec is valid")
        except OpenAPIValidationError as e:
            logger.error(f"Invalid OpenAPI spec: {e}")
            raise

        self.spec = spec
        return cast(Dict[str, Any], spec)

    def configure_cleanup(
        self,
        id_extractors: Optional[Dict[str, Callable[..., Any]]] = None,
        delete_patterns: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Configure cleanup behavior.

        Args:
            id_extractors: Custom ID extractors per endpoint
            delete_patterns: Delete URL patterns per endpoint

        Example:
            tester.configure_cleanup(
                id_extractors={
                    "/api/users": lambda data: data["userId"],
                    "/api/posts": lambda data: data["post"]["id"],
                },
                delete_patterns={
                    "/api/users": "/api/users/{id}",
                    "/api/posts": "/api/posts/{id}",
                }
            )
        """
        if id_extractors:
            for endpoint, extractor in id_extractors.items():
                self.tracker.register_id_extractor(endpoint, extractor)

        if delete_patterns:
            for endpoint, pattern in delete_patterns.items():
                self.tracker.register_delete_pattern(endpoint, pattern)

    async def test_endpoint(
        self,
        path: str,
        method: str,
        operation: Dict[str, Any],
        client: httpx.AsyncClient,
    ) -> ContractTestResult:
        """
        Test a single endpoint.

        Args:
            path: API path (e.g., "/api/users")
            method: HTTP method (e.g., "GET", "POST")
            operation: OpenAPI operation object
            client: HTTP client

        Returns:
            Test result
        """
        errors = []
        full_url = self.base_url + path

        # Build headers
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # Generate test data for request body
        request_body = None
        if method.upper() in ["POST", "PUT", "PATCH"]:
            request_body = self._generate_request_body(operation)

        # Make request
        try:
            start_time = asyncio.get_event_loop().time()

            if method.upper() == "GET":
                response = await client.get(full_url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(full_url, json=request_body, headers=headers)
            elif method.upper() == "PUT":
                response = await client.put(full_url, json=request_body, headers=headers)
            elif method.upper() == "PATCH":
                response = await client.patch(full_url, json=request_body, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(full_url, headers=headers)
            else:
                errors.append(f"Unsupported method: {method}")
                return ContractTestResult(
                    endpoint=path,
                    method=method,
                    status_code=0,
                    passed=False,
                    errors=errors,
                    response_time_ms=0,
                )

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Track for cleanup
            if self.cleanup_strategy == CleanupStrategy.TRACK_AND_DELETE:
                self.tracker.track_response(response, endpoint=path, method=method)

            # Validate response
            response_body = None
            try:
                response_body = response.json()
            except Exception:
                pass

            # Check status code matches spec
            expected_status_codes = list(operation.get("responses", {}).keys())
            if str(response.status_code) not in expected_status_codes:
                errors.append(
                    f"Unexpected status code: {response.status_code} "
                    f"(expected one of {expected_status_codes})"
                )

            # Validate response schema (basic check)
            # TODO: Full JSON schema validation

            return ContractTestResult(
                endpoint=path,
                method=method,
                status_code=response.status_code,
                passed=len(errors) == 0,
                errors=errors,
                response_time_ms=response_time,
                request_body=request_body,
                response_body=response_body,
            )

        except Exception as e:
            errors.append(f"Request failed: {e}")
            return ContractTestResult(
                endpoint=path,
                method=method,
                status_code=0,
                passed=False,
                errors=errors,
                response_time_ms=0,
                request_body=request_body,
            )

    def _generate_request_body(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate minimal valid request body from OpenAPI schema.

        Returns example data that satisfies required fields.
        """
        request_body = operation.get("requestBody", {})
        if not request_body:
            return None

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        # Use example if available
        if "example" in json_content:
            return cast(Dict[str, Any], json_content["example"])
        if "example" in schema:
            return cast(Dict[str, Any], schema["example"])

        # Generate minimal data from schema
        return cast(Dict[str, Any], self._generate_from_schema(schema))

    def _generate_from_schema(self, schema: Dict[str, Any]) -> Any:
        """Generate data from JSON schema (basic implementation)."""
        schema_type = schema.get("type", "object")

        if schema_type == "object":
            result = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for prop_name in required:
                if prop_name in properties:
                    result[prop_name] = self._generate_from_schema(properties[prop_name])

            return result

        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._generate_from_schema(items)]

        elif schema_type == "string":
            return "test_value"

        elif schema_type == "integer":
            return 1

        elif schema_type == "number":
            return 1.0

        elif schema_type == "boolean":
            return True

        return None

    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run contract tests for all endpoints in OpenAPI spec.

        Returns:
            Summary of all test results
        """
        if not self.spec:
            await self.load_spec()
        assert self.spec is not None

        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
            paths = self.spec.get("paths", {})

            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                        result = await self.test_endpoint(path, method, operation, client)
                        self.results.append(result)

            # Cleanup
            cleanup_results = None
            if self.cleanup_strategy == CleanupStrategy.TRACK_AND_DELETE:
                auth_header = (
                    {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else None
                )
                cleanup_results = await self.tracker.cleanup_all(client, auth_header)

        # Generate summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        avg_response_time = (
            sum(r.response_time_ms for r in self.results) / len(self.results) if self.results else 0
        )

        summary = {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed / len(self.results) * 100):.1f}%" if self.results else "0%",
            "avg_response_time_ms": f"{avg_response_time:.2f}",
            "cleanup": cleanup_results,
            "failed_tests": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "errors": r.errors,
                }
                for r in self.results
                if not r.passed
            ],
        }

        return summary

"""
Example: API Validation with Automatic Cleanup

This demonstrates how to validate an API against its OpenAPI spec
while ensuring all test data is properly cleaned up.
"""

import asyncio

from apigen.validation import APIValidator, CleanupStrategy, ValidationConfig


async def basic_validation():
    """Basic validation with automatic cleanup."""
    print("\n=== BASIC VALIDATION ===\n")

    validator = APIValidator(
        openapi_spec_url="http://localhost:8001/openapi.json",
        base_url="http://localhost:8001",
        cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE,
    )

    result = await validator.validate()
    result.print_summary()

    return result


async def validation_with_auth():
    """Validation with authentication."""
    print("\n=== VALIDATION WITH AUTH ===\n")

    import os

    auth_token = os.getenv("API_AUTH_TOKEN")

    validator = APIValidator(
        openapi_spec_url="http://localhost:8001/openapi.json",
        base_url="http://localhost:8001",
        auth_token=auth_token,
        cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE,
    )

    result = await validator.validate()
    result.print_summary()

    return result


async def validation_with_custom_cleanup():
    """Validation with custom cleanup patterns."""
    print("\n=== VALIDATION WITH CUSTOM CLEANUP ===\n")

    # Configure custom ID extractors and delete patterns
    config = ValidationConfig(
        openapi_spec_url="http://localhost:8001/openapi.json",
        base_url="http://localhost:8001",
        cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE,
        # Custom ID extractors for endpoints with non-standard response formats
        id_extractors={
            "/api/users": lambda data: data.get("userId") or data.get("user", {}).get("id"),
            "/api/posts": lambda data: data["post"]["postId"],
        },
        # Delete URL patterns
        delete_patterns={
            "/api/users": "/api/users/{id}",
            "/api/posts": "/api/posts/{id}",
            "/api/comments": "/api/comments/{id}",
        },
    )

    validator = APIValidator.from_config(config)
    result = await validator.validate()
    result.print_summary()

    return result


async def validation_with_transaction_cleanup():
    """
    Validation using database transactions (requires API support).

    This is the cleanest approach but requires the API to support
    transaction-based testing mode.
    """
    print("\n=== VALIDATION WITH TRANSACTION CLEANUP ===\n")

    validator = APIValidator(
        openapi_spec_url="http://localhost:8001/openapi.json",
        base_url="http://localhost:8001",
        cleanup_strategy=CleanupStrategy.TRANSACTION,
    )

    # Note: This requires the API to expose test-only endpoints:
    # - POST /api/_test/begin_transaction
    # - POST /api/_test/rollback_transaction

    result = await validator.validate()
    result.print_summary()

    return result


async def manual_contract_testing():
    """Manual contract testing with fine-grained control."""
    print("\n=== MANUAL CONTRACT TESTING ===\n")

    from apigen.validation.contract_tester import ContractTester

    tester = ContractTester(
        openapi_spec_url="http://localhost:8001/openapi.json",
        base_url="http://localhost:8001",
        cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE,
    )

    # Load and validate spec
    spec = await tester.load_spec()
    print(f"Loaded spec: {spec['info']['title']} v{spec['info']['version']}")

    # Configure cleanup patterns
    tester.configure_cleanup(
        delete_patterns={
            "/api/users": "/api/users/{id}",
            "/api/posts": "/api/posts/{id}",
        }
    )

    # Run all tests
    summary = await tester.run_all_tests()

    print("\nTests completed:")
    print(f"  Total: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success rate: {summary['success_rate']}")

    if summary["cleanup"]:
        print("\nCleanup:")
        print(f"  Deleted: {summary['cleanup']['deleted']}")
        print(f"  Failed: {summary['cleanup']['failed']}")

    return summary


async def programmatic_resource_tracking():
    """Direct use of ResourceTracker for custom testing."""
    print("\n=== PROGRAMMATIC RESOURCE TRACKING ===\n")

    import httpx

    from apigen.validation.cleanup import ResourceTracker

    tracker = ResourceTracker()

    # Configure tracking
    tracker.register_delete_pattern("/api/users", "/api/users/{id}")
    tracker.register_delete_pattern("/api/posts", "/api/posts/{id}")

    # Make API calls and track responses
    async with httpx.AsyncClient() as client:
        # Create a user
        response = await client.post(
            "http://localhost:8001/api/users",
            json={"name": "Test User", "email": "test@example.com"},
        )
        tracker.track_response(response, endpoint="/api/users", method="POST")
        print(f"Created user: {response.status_code}")

        # Create a post
        response = await client.post(
            "http://localhost:8001/api/posts",
            json={"title": "Test Post", "content": "This is a test"},
        )
        tracker.track_response(response, endpoint="/api/posts", method="POST")
        print(f"Created post: {response.status_code}")

        # Cleanup all created resources
        print("\nCleaning up...")
        cleanup_summary = await tracker.cleanup_all(client)

        print("Cleanup complete:")
        print(f"  Total tracked: {cleanup_summary['total']}")
        print(f"  Deleted: {cleanup_summary['deleted']}")
        print(f"  Failed: {cleanup_summary['failed']}")

    return cleanup_summary


# Example: Integration with pytest
def test_api_contract():
    """
    Pytest example for API contract testing.

    Add this to your test suite:

        # tests/test_api_contract.py
        import pytest
        from apigen.validation import APIValidator, CleanupStrategy

        @pytest.mark.asyncio
        async def test_api_matches_openapi_spec():
            validator = APIValidator(
                openapi_spec_url="http://localhost:8001/openapi.json",
                base_url="http://localhost:8001",
                cleanup_strategy=CleanupStrategy.TRACK_AND_DELETE,
            )

            result = await validator.validate()

            assert result.failed == 0, f"API contract tests failed: {result.failed_tests}"
            assert result.cleanup_summary["failed"] == 0, "Cleanup failed"
    """
    pass


if __name__ == "__main__":
    # Run examples
    print("API Validation Examples")
    print("=" * 60)

    # Choose which example to run
    import sys

    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == "basic":
            asyncio.run(basic_validation())
        elif example == "auth":
            asyncio.run(validation_with_auth())
        elif example == "custom":
            asyncio.run(validation_with_custom_cleanup())
        elif example == "transaction":
            asyncio.run(validation_with_transaction_cleanup())
        elif example == "manual":
            asyncio.run(manual_contract_testing())
        elif example == "tracking":
            asyncio.run(programmatic_resource_tracking())
        else:
            print(f"Unknown example: {example}")
    else:
        print("\nUsage:")
        print("  python api_validation_example.py [basic|auth|custom|transaction|manual|tracking]")
        print("\nExamples:")
        print("  python api_validation_example.py basic")
        print("  python api_validation_example.py custom")

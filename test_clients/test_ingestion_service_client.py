#!/usr/bin/env python3
"""
Test script for the generated ingestion_service client.

Tests the auto-generated client against the live Ingestion Microservice.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion_service import IngestionServiceClient


async def test_client():
    """Test the generated client against the Ingestion Microservice."""
    print("=" * 80)
    print("Testing Generated Ingestion Microservice Client")
    print("=" * 80)

    # Get configuration from environment
    base_url = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8000")

    # Check for SSL verification flag
    verify_ssl = os.getenv("SSL_VERIFY", "true").lower() != "false"
    if not verify_ssl:
        print("\n⚠️  SSL verification disabled (set SSL_VERIFY=true to enable)")

    print(f"\nBase URL: {base_url}")
    print(f"SSL Verification: {verify_ssl}")

    # Create client instance
    client = IngestionServiceClient(
        base_url=base_url,
        timeout=30.0,
        verify_ssl=verify_ssl,
    )

    success_count = 0
    failure_count = 0
    test_number = 0

    async with client:
        test_number += 1
        print(f"\n{test_number}. Testing Health Check")
        print("-" * 80)
        try:
            result = await client.health_check_health_get()
            print("✓ Health Check: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ Health Check Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing Detailed Health Check")
        print("-" * 80)
        try:
            result = await client.detailed_health_check_health_detailed_get()
            print("✓ Detailed Health Check: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ Detailed Health Check Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing Readiness Check")
        print("-" * 80)
        try:
            result = await client.readiness_check_health_ready_get()
            print("✓ Readiness Check: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ Readiness Check Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing Liveness Check")
        print("-" * 80)
        try:
            result = await client.liveness_check_health_live_get()
            print("✓ Liveness Check: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ Liveness Check Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing List Jobs")
        print("-" * 80)
        try:
            result = await client.list_jobs_jobs_get()
            print("✓ List Jobs: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ List Jobs Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing Get Supported Formats")
        print("-" * 80)
        try:
            result = await client.get_supported_formats_formats_get()
            print("✓ Get Supported Formats: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ Get Supported Formats Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing List Sessions")
        print("-" * 80)
        try:
            result = await client.list_sessions_scrape_sessions_get()
            print("✓ List Sessions: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ List Sessions Failed: {type(e).__name__}: {e}")
            failure_count += 1
        test_number += 1
        print(f"\n{test_number}. Testing Root")
        print("-" * 80)
        try:
            result = await client.root__get()
            print("✓ Root: Success")

            # Print result preview
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
                if isinstance(result_dict, dict) and result_dict:
                    print("  Response preview:")
                    for key, value in list(result_dict.items())[:5]:
                        val_str = str(value)[:100]
                        print(f"    {key}: {val_str}")
            elif isinstance(result, dict):
                print("  Response preview:")
                for key, value in list(result.items())[:5]:
                    val_str = str(value)[:100]
                    print(f"    {key}: {val_str}")
            elif result is not None:
                print(f"  Result: {str(result)[:200]}")

            success_count += 1
        except Exception as e:
            print(f"✗ Root Failed: {type(e).__name__}: {e}")
            failure_count += 1

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total Tests: {test_number}")
    print(f"Passed: {success_count}")
    print(f"Failed: {failure_count}")

    if failure_count == 0:
        print("\n✓ All tests passed!")
        print("=" * 80)
        return True
    else:
        print(f"\n✗ {failure_count} test(s) failed")
        print("=" * 80)
        return False


async def main():
    """Main entry point."""
    try:
        success = await test_client()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

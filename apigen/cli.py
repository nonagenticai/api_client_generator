"""Command-line interface for apigen."""

import sys
from pathlib import Path
from typing import Optional

import click

from apigen.core.code_gen import PydanticClientGenerator
from apigen.parsers.openapi.parser import OpenAPIParser


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """apigen - Modern OpenAPI client generator with Pydantic v2."""
    pass


@cli.command()
@click.argument("spec_path")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="clients",
    help="Output directory for generated client",
)
@click.option(
    "--name",
    "-n",
    type=str,
    help="Service name (defaults to title from spec)",
)
@click.option(
    "--no-format",
    is_flag=True,
    help="Skip code formatting with black/isort",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip OpenAPI spec validation (use with caution)",
)
@click.option(
    "--insecure",
    is_flag=True,
    help="Disable SSL certificate verification (for self-signed certificates)",
)
@click.option(
    "--no-tests",
    is_flag=True,
    help="Skip generating test file",
)
def generate(
    spec_path: str,
    output: str,
    name: Optional[str],
    no_format: bool,
    skip_validation: bool,
    insecure: bool,
    no_tests: bool,
) -> None:
    """
    Generate API client from OpenAPI specification.

    SPEC_PATH: Path or URL to OpenAPI specification (JSON or YAML)

    Examples:

        \b
        # From local file
        apigen generate ./openapi.json

        \b
        # From URL
        apigen generate https://api.example.com/openapi.json

        \b
        # With custom name and output
        apigen generate ./spec.yaml --name my_api --output ./generated
    """
    click.echo(f"📖 Loading OpenAPI spec from: {spec_path}")

    if insecure:
        click.secho("⚠️  SSL verification disabled (insecure mode)", fg="yellow")

    try:
        # Parse OpenAPI spec
        parser = OpenAPIParser(verify_ssl=not insecure)

        # Validate first (unless skipped)
        if not skip_validation:
            errors = parser.validate(spec_path)
            if errors:
                click.secho("❌ Validation failed:", fg="red")
                for error in errors:
                    click.echo(f"  • {error}")
                click.echo("\n💡 Tip: Use --skip-validation to generate anyway (may have issues)")
                sys.exit(1)
        else:
            click.secho("⚠️  Skipping validation", fg="yellow")

        # Parse to IR
        api_spec = parser.parse(spec_path, service_name=name)

        click.echo(f"✓ Parsed {api_spec.title} v{api_spec.version}")
        click.echo(f"  • {len(api_spec.endpoints)} endpoints")
        click.echo(f"  • {len(api_spec.models)} models")

        # Generate client
        output_dir = Path(output)
        generator = PydanticClientGenerator(output_dir)

        click.echo("\n🔧 Generating client...")
        client_path = generator.generate(
            api_spec, format_code=not no_format, generate_tests=not no_tests
        )

        click.secho(f"\n✓ Generated client at: {client_path}", fg="green")

        if not no_tests:
            test_file = output_dir / f"test_{api_spec.name}_client.py"
            if test_file.exists():
                click.secho(f"✓ Generated test at: {test_file}", fg="green")

        click.echo("\n📦 Usage:")
        click.echo(f"  from {client_path.name} import get_client")
        click.echo("  async with get_client() as client:")
        click.echo("      # Use the client")

        if not no_tests:
            click.echo("\n🧪 Run tests:")
            click.echo(f"  SSL_VERIFY=false python test_{api_spec.name}_client.py")

    except FileNotFoundError as e:
        click.secho(f"❌ File not found: {e}", fg="red")
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        import traceback

        if "--verbose" in sys.argv:
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("spec_path")
@click.option(
    "--insecure",
    is_flag=True,
    help="Disable SSL certificate verification (for self-signed certificates)",
)
def validate(spec_path: str, insecure: bool) -> None:
    """
    Validate OpenAPI specification.

    SPEC_PATH: Path or URL to OpenAPI specification
    """
    click.echo(f"📖 Validating spec: {spec_path}")

    if insecure:
        click.secho("⚠️  SSL verification disabled (insecure mode)", fg="yellow")

    try:
        parser = OpenAPIParser(verify_ssl=not insecure)

        # Check if it's OpenAPI
        if not parser.is_openapi_spec(spec_path):
            click.secho("❌ Not a valid OpenAPI 3.x specification", fg="red")
            sys.exit(1)

        # Validate
        errors = parser.validate(spec_path)

        if errors:
            click.secho("❌ Validation failed:", fg="red")
            for error in errors:
                click.echo(f"  • {error}")
            sys.exit(1)
        else:
            click.secho("✓ Specification is valid", fg="green")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("spec_path")
@click.option(
    "--insecure",
    is_flag=True,
    help="Disable SSL certificate verification (for self-signed certificates)",
)
def info(spec_path: str, insecure: bool) -> None:
    """
    Show information about an OpenAPI specification.

    SPEC_PATH: Path or URL to OpenAPI specification
    """
    if insecure:
        click.secho("⚠️  SSL verification disabled (insecure mode)", fg="yellow")

    try:
        parser = OpenAPIParser(verify_ssl=not insecure)
        api_spec = parser.parse(spec_path)

        click.echo("=" * 60)
        click.secho(f"📊 {api_spec.title}", fg="cyan", bold=True)
        click.echo("=" * 60)
        click.echo(f"Version:     {api_spec.version}")
        click.echo(f"Name:        {api_spec.name}")
        if api_spec.base_url:
            click.echo(f"Base URL:    {api_spec.base_url}")
        if api_spec.description:
            click.echo(f"Description: {api_spec.description}")

        click.echo("\n📈 Statistics:")
        click.echo(f"  • Endpoints: {len(api_spec.endpoints)}")
        click.echo(f"  • Models:    {len(api_spec.models)}")

        if api_spec.auth_config.auth_type.value != "none":
            click.echo("\n🔐 Authentication:")
            click.echo(f"  • Type: {api_spec.auth_config.auth_type.value}")

        if api_spec.endpoints:
            click.echo("\n📍 Endpoints:")
            for endpoint in api_spec.endpoints[:10]:  # Show first 10
                click.echo(f"  • {endpoint.http_method.value:6} {endpoint.path}")
                click.echo(f"           {endpoint.summary or endpoint.description or ''}")

            if len(api_spec.endpoints) > 10:
                click.echo(f"  ... and {len(api_spec.endpoints) - 10} more")

        if api_spec.models:
            click.echo("\n🏗️  Models:")
            for model in api_spec.models[:10]:  # Show first 10
                click.echo(f"  • {model.name}")
                if model.description:
                    click.echo(f"      {model.description}")

            if len(api_spec.models) > 10:
                click.echo(f"  ... and {len(api_spec.models) - 10} more")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("spec_url")
@click.argument("base_url")
@click.option(
    "--auth-token",
    "-t",
    envvar="API_AUTH_TOKEN",
    help="Authentication token (can also use API_AUTH_TOKEN env var)",
)
@click.option(
    "--cleanup",
    "-c",
    type=click.Choice(["track_and_delete", "transaction", "test_database", "none"]),
    default="track_and_delete",
    help="Cleanup strategy for test data",
)
@click.option(
    "--timeout",
    type=float,
    default=30.0,
    help="Request timeout in seconds",
)
@click.option(
    "--insecure",
    is_flag=True,
    help="Disable SSL certificate verification (for self-signed certificates)",
)
def test(
    spec_url: str,
    base_url: str,
    auth_token: Optional[str],
    cleanup: str,
    timeout: float,
    insecure: bool,
) -> None:
    """
    Test API against its OpenAPI specification with automatic cleanup.

    SPEC_URL: URL to OpenAPI specification (e.g., http://localhost:8001/openapi.json)
    BASE_URL: Base URL of API to test (e.g., http://localhost:8001)

    This validates that your API actually works as documented in the OpenAPI spec
    and automatically cleans up any test data created during validation.

    Examples:

        \b
        # Test local API
        apigen test http://localhost:8001/openapi.json http://localhost:8001

        \b
        # With authentication
        apigen test http://api.example.com/openapi.json http://api.example.com \\
            --auth-token "your-token-here"

        \b
        # Using environment variable for auth
        export API_AUTH_TOKEN="your-token"
        apigen test http://api.example.com/openapi.json http://api.example.com
    """
    import asyncio

    from apigen.validation import APIValidator, CleanupStrategy

    click.echo(f"🧪 Testing API: {base_url}")
    click.echo(f"📖 Using spec: {spec_url}")
    click.echo(f"🧹 Cleanup strategy: {cleanup}\n")

    if insecure:
        click.secho("⚠️  SSL verification disabled (insecure mode)", fg="yellow")

    try:
        validator = APIValidator(
            openapi_spec_url=spec_url,
            base_url=base_url,
            auth_token=auth_token,
            cleanup_strategy=CleanupStrategy(cleanup),
            verify_ssl=not insecure,
        )

        # Run validation
        result = asyncio.run(validator.validate())

        # Print results
        result.print_summary()

        # Exit with error code if tests failed
        if result.failed > 0:
            sys.exit(1)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        import traceback

        if "--verbose" in sys.argv:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()

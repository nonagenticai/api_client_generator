"""Pydantic v2 code generator."""

import subprocess
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from apigen.core.ir import APISpec
from apigen.utils.naming import sanitize_class_name


class PydanticClientGenerator:
    """Generates Pydantic v2 clients from IR."""

    def __init__(self, output_dir: Path, template_dir: Optional[Path] = None):
        """
        Initialize the generator.

        Args:
            output_dir: Base directory for generated clients
            template_dir: Directory containing Jinja2 templates (defaults to package templates)
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up Jinja2 environment
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["repr"] = repr

    def generate(
        self, spec: APISpec, format_code: bool = True, generate_tests: bool = True
    ) -> Path:
        """
        Generate complete client package from API spec.

        Args:
            spec: API specification (IR)
            format_code: Whether to format generated code with black/isort
            generate_tests: Whether to generate test file

        Returns:
            Path to generated client directory
        """
        client_dir = self.output_dir / spec.name
        client_dir.mkdir(parents=True, exist_ok=True)

        # Generate models.py
        self._generate_models(spec, client_dir / "models.py")

        # Generate client.py
        self._generate_client(spec, client_dir / "client.py")

        # Generate singleton.py
        self._generate_singleton(spec, client_dir / "singleton.py")

        # Generate __init__.py
        self._generate_init(spec, client_dir / "__init__.py")

        # Generate test file
        if generate_tests:
            self._generate_test(spec, self.output_dir / f"test_{spec.name}_client.py")

        # Format code
        if format_code:
            self._format_code(client_dir)

        return client_dir

    def _generate_models(self, spec: APISpec, output_file: Path) -> None:
        """Generate Pydantic v2 models."""
        template = self.env.get_template("models.py.jinja")

        # Check if we need special imports
        has_email = any(
            field.type_info.python_type == "EmailStr"
            for model in spec.models
            for field in model.fields
        )
        has_url = any(
            field.type_info.python_type == "AnyUrl"
            for model in spec.models
            for field in model.fields
        )

        content = template.render(
            service_name=spec.name,
            models=spec.models,
            has_email=has_email,
            has_url=has_url,
        )
        output_file.write_text(content)

    def _generate_client(self, spec: APISpec, output_file: Path) -> None:
        """Generate async HTTP client."""
        template = self.env.get_template("client.py.jinja")

        client_class_name = sanitize_class_name(spec.name) + "Client"

        content = template.render(
            service_name=spec.name,
            title=spec.title,
            description=spec.description,
            client_class_name=client_class_name,
            endpoints=spec.endpoints,
            auth_type=spec.auth_config.auth_type.value,
            api_key_header=spec.auth_config.api_key_header,
        )
        output_file.write_text(content)

    def _generate_singleton(self, spec: APISpec, output_file: Path) -> None:
        """Generate singleton factory."""
        template = self.env.get_template("singleton.py.jinja")

        client_class_name = sanitize_class_name(spec.name) + "Client"
        url_env_var = spec.auth_config.url_env_var or f"{spec.name.upper()}_URL"
        token_env_var = spec.auth_config.token_env_var or f"{spec.name.upper()}_TOKEN"
        default_url = spec.base_url or "http://localhost:8000"

        content = template.render(
            service_name=spec.name,
            client_class_name=client_class_name,
            url_env_var=url_env_var,
            token_env_var=token_env_var,
            default_url=default_url,
        )
        output_file.write_text(content)

    def _generate_init(self, spec: APISpec, output_file: Path) -> None:
        """Generate package __init__.py."""
        template = self.env.get_template("package_init.py.jinja")

        client_class_name = sanitize_class_name(spec.name) + "Client"

        content = template.render(
            service_name=spec.name,
            title=spec.title,
            client_class_name=client_class_name,
        )
        output_file.write_text(content)

    def _generate_test(self, spec: APISpec, output_file: Path) -> None:
        """Generate test file for the client."""
        template = self.env.get_template("test_client.py.jinja")

        client_class_name = sanitize_class_name(spec.name) + "Client"
        url_env_var = spec.auth_config.url_env_var or f"{spec.name.upper()}_URL"
        token_env_var = spec.auth_config.token_env_var or f"{spec.name.upper()}_TOKEN"
        default_url = spec.base_url or "http://localhost:8000"

        # Select a few key endpoints to test (GET endpoints without required params)
        test_endpoints = []
        for endpoint in spec.endpoints:
            # Prioritize health/status endpoints
            if any(
                tag in ["health", "status", "system"] for tag in [t.lower() for t in endpoint.tags]
            ):
                test_endpoints.append(endpoint)
            # Also include simple GET endpoints
            elif endpoint.http_method.value == "GET" and not any(
                p.required for p in endpoint.parameters
            ):
                test_endpoints.append(endpoint)

        # Limit to first 10 endpoints to keep tests manageable
        test_endpoints = test_endpoints[:10]

        content = template.render(
            service_name=spec.name,
            title=spec.title,
            client_class_name=client_class_name,
            url_env_var=url_env_var,
            token_env_var=token_env_var,
            default_url=default_url,
            auth_type=spec.auth_config.auth_type.value,
            test_endpoints=test_endpoints,
        )
        output_file.write_text(content)

    def _format_code(self, directory: Path) -> None:
        """Format generated code with black and isort."""
        try:
            # Format with black
            subprocess.run(
                ["black", str(directory)],
                capture_output=True,
                check=False,
            )

            # Sort imports with isort
            subprocess.run(
                ["isort", str(directory)],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            # black/isort not installed, skip formatting
            pass

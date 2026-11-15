"""OpenAPI 3.x specification parser."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import requests
import yaml
from openapi_spec_validator import validate_spec

from apigen.core.ir import (
    APISpec,
    AuthConfig,
    AuthType,
    Endpoint,
    HTTPMethod,
    Model,
    ModelField,
    Parameter,
    ParameterLocation,
    TypeCategory,
    TypeInfo,
)
from apigen.utils.naming import (
    sanitize_class_name,
    sanitize_field_name,
    sanitize_method_name,
    sanitize_package_name,
)


class OpenAPIParser:
    """
    Parser for OpenAPI 3.x specifications.

    Supports OpenAPI 3.0.x, 3.1.x, and designed to handle future versions.
    """

    SUPPORTED_VERSIONS = ["3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.1.0"]

    def __init__(self, verify_ssl: bool = True) -> None:
        """
        Initialize the parser.

        Args:
            verify_ssl: Whether to verify SSL certificates when fetching URLs.
                       Set to False for self-signed certificates.
        """
        self._schema_cache: Dict[str, Model] = {}
        self._verify_ssl = verify_ssl

    def is_openapi_spec(self, spec: Union[str, Path, Dict[str, Any]]) -> bool:
        """Check if spec is an OpenAPI 3.x specification."""
        try:
            data = self._load_spec(spec)
            return "openapi" in data and data["openapi"].startswith("3.")
        except Exception:
            return False

    def validate(self, spec: Union[str, Path, Dict[str, Any]]) -> List[str]:
        """
        Validate OpenAPI spec and return list of errors.

        Returns:
            List of error messages (empty list if valid)
        """
        try:
            data = self._load_spec(spec)
            validate_spec(data)
            return []
        except Exception as e:
            return [str(e)]

    def parse(
        self, spec: Union[str, Path, Dict[str, Any]], service_name: Optional[str] = None
    ) -> APISpec:
        """
        Parse OpenAPI spec into Intermediate Representation.

        Args:
            spec: Spec as file path, URL, or dict
            service_name: Optional service name override

        Returns:
            APISpec object (Intermediate Representation)
        """
        data = self._load_spec(spec)

        # Extract basic info
        info = data.get("info", {})
        title = info.get("title", "Unknown API")
        version = info.get("version", "0.1.0")
        description = info.get("description")

        # Sanitize name (for package naming)
        name = service_name or sanitize_package_name(title)

        # Parse servers for base URL
        servers = data.get("servers", [])
        base_url = servers[0]["url"] if servers else None

        # Parse components/schemas → models
        components = data.get("components", {})
        schemas = components.get("schemas", {})
        models = self._parse_schemas(schemas)

        # Parse paths → endpoints
        paths = data.get("paths", {})
        endpoints = self._parse_paths(paths)

        # Parse security
        auth_config = self._parse_security(data, name)

        return APISpec(
            name=name,
            title=title,
            version=version,
            description=description,
            base_url=base_url,
            endpoints=endpoints,
            models=models,
            auth_config=auth_config,
            original_spec_type="openapi",
            original_spec_version=data.get("openapi"),
        )

    # =========================================================================
    # Private helper methods
    # =========================================================================

    def _load_spec(self, spec: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Load spec from file, URL, or dict."""
        # Already a dict
        if isinstance(spec, dict):
            return spec

        # File path
        if isinstance(spec, (str, Path)) and not str(spec).startswith(("http://", "https://")):
            path = Path(spec)
            if not path.exists():
                raise FileNotFoundError(f"Spec file not found: {path}")

            content = path.read_text()

            # Determine format from extension
            if path.suffix in [".yaml", ".yml"]:
                return cast(Dict[str, Any], yaml.safe_load(content))
            elif path.suffix == ".json":
                return cast(Dict[str, Any], json.loads(content))
            else:
                # Try YAML first, then JSON
                try:
                    return cast(Dict[str, Any], yaml.safe_load(content))
                except yaml.YAMLError:
                    return cast(Dict[str, Any], json.loads(content))

        # URL
        if isinstance(spec, str) and spec.startswith(("http://", "https://")):
            response = requests.get(spec, timeout=30, verify=self._verify_ssl)
            response.raise_for_status()

            # Try to parse as JSON
            try:
                return cast(Dict[str, Any], response.json())
            except json.JSONDecodeError:
                # Try YAML
                return cast(Dict[str, Any], yaml.safe_load(response.text))

        raise ValueError(f"Invalid spec format: {type(spec)}")

    def _parse_schemas(self, schemas: Dict[str, Any]) -> List[Model]:
        """Parse OpenAPI schemas to Model objects."""
        models = []

        for schema_name, schema_def in schemas.items():
            model = self._parse_schema(schema_name, schema_def)
            if model:
                models.append(model)
                self._schema_cache[schema_name] = model

        return models

    def _parse_schema(self, name: str, schema: Dict[str, Any]) -> Optional[Model]:
        """Parse a single schema to a Model."""
        schema_type = schema.get("type")

        # Handle enum schemas as Python Enum classes
        if "enum" in schema:
            enum_values = schema["enum"]
            return Model(
                name=sanitize_class_name(name),
                fields=[],
                description=schema.get("description"),
                is_enum=True,
                enum_values=enum_values,
                enum_type=self._map_openapi_type(schema_type or "string", None),
            )

        # Only handle object schemas as models
        # Primitives and arrays are handled inline
        if schema_type != "object":
            return None

        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        fields = []
        for field_name, field_schema in properties.items():
            type_info = self._parse_type(field_schema)
            python_name = sanitize_field_name(field_name)
            field = ModelField(
                name=python_name,
                # Keep the wire name whenever sanitizing changed it (keywords like
                # "id" -> "id_", camelCase -> snake_case, "user-id" -> "user_id"),
                # otherwise the model rejects/drops real payloads.
                alias=field_name if python_name != field_name else None,
                type_info=type_info,
                required=field_name in required_fields,
                description=field_schema.get("description"),
            )
            fields.append(field)

        return Model(
            name=sanitize_class_name(name),
            fields=fields,
            description=schema.get("description"),
        )

    def _parse_type(self, schema: Dict[str, Any]) -> TypeInfo:
        """Parse OpenAPI schema to TypeInfo."""
        # Handle $ref
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            return TypeInfo(
                category=TypeCategory.OBJECT,
                python_type="object",
                model_name=sanitize_class_name(ref_name),
                description=schema.get("description"),
            )

        # Handle allOf, oneOf, anyOf (union types)
        if "anyOf" in schema or "oneOf" in schema:
            union_schemas = schema.get("anyOf") or schema.get("oneOf", [])
            union_types = [self._parse_type(s) for s in union_schemas]
            return TypeInfo(
                category=TypeCategory.UNION,
                python_type="Union",
                union_types=union_types,
                description=schema.get("description"),
            )

        # Handle array
        if schema.get("type") == "array":
            items = schema.get("items", {})
            item_type = self._parse_type(items)
            return TypeInfo(
                category=TypeCategory.ARRAY,
                python_type=item_type.python_type,
                is_array=True,
                array_item_type=item_type,
                description=schema.get("description"),
            )

        # Handle nullable (OpenAPI 3.0) or null in type array (OpenAPI 3.1)
        is_nullable = schema.get("nullable", False)
        schema_type = schema.get("type", "string")

        # OpenAPI 3.1 can have type as array
        if isinstance(schema_type, list):
            if "null" in schema_type:
                is_nullable = True
                # Get the non-null type
                schema_type = next((t for t in schema_type if t != "null"), "string")

        # Handle primitives
        python_type = self._map_openapi_type(schema_type, schema.get("format"))

        # Extract constraints
        constraints = {}
        if "minimum" in schema:
            constraints["ge"] = schema["minimum"]
        if "maximum" in schema:
            constraints["le"] = schema["maximum"]
        if "minLength" in schema:
            constraints["min_length"] = schema["minLength"]
        if "maxLength" in schema:
            constraints["max_length"] = schema["maxLength"]
        if "pattern" in schema:
            constraints["pattern"] = schema["pattern"]
        if "minItems" in schema:
            constraints["min_length"] = schema["minItems"]
        if "maxItems" in schema:
            constraints["max_length"] = schema["maxItems"]

        # Handle enums
        enum_values = schema.get("enum", [])
        category = TypeCategory.ENUM if enum_values else TypeCategory.PRIMITIVE

        return TypeInfo(
            category=category,
            python_type=python_type,
            is_optional=is_nullable,
            enum_values=enum_values,
            constraints=constraints,
            description=schema.get("description"),
            example=schema.get("example"),
        )

    def _map_openapi_type(self, openapi_type: str, format_: Optional[str] = None) -> str:
        """Map OpenAPI type to Python type."""
        # Handle special formats
        if format_ == "date-time":
            return "datetime"
        elif format_ == "date":
            return "date"
        elif format_ == "uuid":
            return "UUID"
        elif format_ == "email":
            return "EmailStr"
        elif format_ == "uri":
            return "AnyUrl"
        elif format_ == "binary":
            return "bytes"

        # Handle basic types
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "object": "Dict[str, Any]",
            "array": "list",
        }

        return type_map.get(openapi_type, "Any")

    def _parse_paths(self, paths: Dict[str, Any]) -> List[Endpoint]:
        """Parse OpenAPI paths to Endpoint objects."""
        endpoints = []

        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() not in [m.value for m in HTTPMethod]:
                    continue

                endpoint = self._parse_operation(path, method.upper(), operation)
                if endpoint:
                    endpoints.append(endpoint)

        return endpoints

    def _parse_operation(self, path: str, method: str, operation: Dict[str, Any]) -> Endpoint:
        """Parse a single operation to an Endpoint."""
        operation_id = operation.get(
            "operationId",
            f"{method.lower()}{path.replace('/', '_').replace('{', '').replace('}', '')}",
        )
        summary = operation.get("summary", "")
        description = operation.get("description", "")
        tags = operation.get("tags", [])
        deprecated = operation.get("deprecated", False)

        # Parse parameters
        parameters = []
        for param in operation.get("parameters", []):
            parameters.append(self._parse_parameter(param))

        # Parse request body
        request_body = None
        request_body_required = False
        if "requestBody" in operation:
            request_body_obj = operation["requestBody"]
            request_body_required = request_body_obj.get("required", False)
            content = request_body_obj.get("content", {})

            # Prefer application/json
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                request_body = self._parse_type(schema)
            elif content:
                # Use first available content type
                first_content = next(iter(content.values()))
                schema = first_content.get("schema", {})
                request_body = self._parse_type(schema)

        # Parse responses
        responses = operation.get("responses", {})
        response_type = self._parse_response(responses)

        return Endpoint(
            operation_id=operation_id,
            name=summary or sanitize_method_name(operation_id),
            path=path,
            http_method=HTTPMethod(method),
            parameters=parameters,
            request_body=request_body,
            request_body_required=request_body_required,
            response_type=response_type,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
        )

    def _parse_parameter(self, param: Dict[str, Any]) -> Parameter:
        """Parse OpenAPI parameter to Parameter object."""
        name = param["name"]
        location = param["in"]  # "query", "path", "header", etc.
        required = param.get("required", location == "path")  # Path params always required
        description = param.get("description")

        schema = param.get("schema", {})
        type_info = self._parse_type(schema)

        python_name = sanitize_field_name(name)
        return Parameter(
            name=python_name,
            wire_name=name if python_name != name else None,
            location=ParameterLocation(location),
            type_info=type_info,
            required=required,
            description=description,
        )

    def _parse_response(self, responses: Dict[str, Any]) -> TypeInfo:
        """Parse response schema (prioritize 200/201/2XX)."""
        # Try success status codes in order
        for status in ["200", "201", "2XX", "default"]:
            if status in responses:
                response = responses[status]
                content = response.get("content", {})

                # Prefer application/json
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    return self._parse_type(schema)
                elif content:
                    # Use first available content type
                    first_content = next(iter(content.values()))
                    schema = first_content.get("schema", {})
                    return self._parse_type(schema)

        # No response body
        return TypeInfo(category=TypeCategory.PRIMITIVE, python_type="None")

    def _parse_security(self, data: Dict[str, Any], service_name: str) -> AuthConfig:
        """Parse security schemes from OpenAPI spec."""
        components = data.get("components", {})
        security_schemes = components.get("securitySchemes", {})

        if not security_schemes:
            return AuthConfig(auth_type=AuthType.NONE)

        # Find first scheme (usually there's only one)
        for scheme_name, scheme in security_schemes.items():
            scheme_type = scheme.get("type", "").lower()

            if scheme_type == "http":
                http_scheme = scheme.get("scheme", "").lower()
                if http_scheme == "bearer":
                    return AuthConfig(
                        auth_type=AuthType.BEARER,
                        token_env_var=f"{service_name.upper()}_TOKEN",
                        url_env_var=f"{service_name.upper()}_URL",
                    )
                elif http_scheme == "basic":
                    return AuthConfig(auth_type=AuthType.BASIC)

            elif scheme_type == "apikey":
                return AuthConfig(
                    auth_type=AuthType.API_KEY,
                    api_key_header=scheme.get("name", "X-API-Key"),
                    token_env_var=f"{service_name.upper()}_TOKEN",
                    url_env_var=f"{service_name.upper()}_URL",
                )

            elif scheme_type == "oauth2":
                return AuthConfig(
                    auth_type=AuthType.OAUTH2,
                    oauth2_flows=scheme.get("flows", {}),
                )

        return AuthConfig(auth_type=AuthType.NONE)

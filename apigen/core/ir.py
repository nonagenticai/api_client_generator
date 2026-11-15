"""
Intermediate Representation (IR) for OpenAPI specifications.

The IR is a unified data structure that represents any OpenAPI spec version,
allowing us to generate consistent Pydantic v2 clients regardless of whether
the source is OpenAPI 3.0, 3.1, or future versions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TypeCategory(str, Enum):
    """High-level type categories for API types."""

    PRIMITIVE = "primitive"  # str, int, bool, float
    ARRAY = "array"  # List[T]
    OBJECT = "object"  # Dict or custom model
    UNION = "union"  # Union[A, B]
    ENUM = "enum"  # Literal["a", "b"]
    ANY = "any"  # Any type


class TypeInfo(BaseModel):
    """
    Type information that maps to Python/Pydantic types.

    Examples:
        - str: TypeInfo(category="primitive", python_type="str")
        - int (1-100): TypeInfo(category="primitive", python_type="int", constraints={"ge": 1, "le": 100})
        - List[str]: TypeInfo(category="array", python_type="str", is_array=True)
        - Optional[str]: TypeInfo(category="primitive", python_type="str", is_optional=True)
    """

    model_config = ConfigDict(frozen=False)

    category: TypeCategory
    python_type: str  # Base Python type: "str", "int", "bool", "float", "dict", etc.

    # Optionality
    is_optional: bool = False
    default: Optional[Any] = None

    # Array handling
    is_array: bool = False
    array_item_type: Optional[TypeInfo] = None

    # Object/Model handling
    model_name: Optional[str] = None  # If this is a custom model reference

    # Union handling
    union_types: List[TypeInfo] = Field(default_factory=list)

    # Enum handling
    enum_values: List[Any] = Field(default_factory=list)

    # Validation constraints (maps to Pydantic Field constraints)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    # Examples: {"min_length": 5, "max_length": 100, "pattern": r"^\w+$", "ge": 0, "le": 100}

    # Documentation
    description: Optional[str] = None
    example: Optional[Any] = None

    def to_python_type_hint(self) -> str:
        """Generate Python type hint string."""
        if self.is_array:
            item_hint = (
                self.array_item_type.to_python_type_hint() if self.array_item_type else "Any"
            )
            base = f"List[{item_hint}]"
        elif self.category == TypeCategory.UNION and self.union_types:
            union_parts = [t.to_python_type_hint() for t in self.union_types]
            base = f"Union[{', '.join(union_parts)}]"
        elif self.category == TypeCategory.ENUM and self.enum_values:
            enum_parts = ", ".join(repr(v) for v in self.enum_values)
            base = f"Literal[{enum_parts}]"
        elif self.model_name:
            base = self.model_name
        else:
            base = self.python_type

        if self.is_optional:
            return f"Optional[{base}]"
        return base


class ParameterLocation(str, Enum):
    """Where the parameter appears in the HTTP request."""

    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


class Parameter(BaseModel):
    """
    API parameter (query string, path param, header, etc.)

    Examples:
        - Query: ?limit=10 → Parameter(name="limit", location="query", ...)
        - Path: /users/{id} → Parameter(name="id", location="path", ...)
    """

    model_config = ConfigDict(frozen=False)

    name: str  # Python identifier (sanitized, e.g. "id_")
    location: ParameterLocation
    type_info: TypeInfo
    wire_name: Optional[str] = None  # Name on the wire when it differs from `name` (e.g. "id")
    required: bool = True
    description: Optional[str] = None
    deprecated: bool = False

    @property
    def key(self) -> str:
        """Name used on the wire (path placeholder, query key, header name)."""
        return self.wire_name or self.name


class HTTPMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class Endpoint(BaseModel):
    """
    Single API endpoint/operation.

    Examples:
        - GET /users → Endpoint(name="get_users", path="/users", http_method="GET", ...)
        - POST /users → Endpoint(name="create_user", path="/users", http_method="POST", ...)
    """

    model_config = ConfigDict(frozen=False)

    # Identification
    operation_id: str  # Unique operation ID (becomes method name)
    name: str  # Human-readable name
    path: str  # URL path (e.g., "/api/v1/users/{id}")
    http_method: HTTPMethod

    # Parameters
    parameters: List[Parameter] = Field(default_factory=list)

    # Request body (for POST, PUT, PATCH)
    request_body: Optional[TypeInfo] = None
    request_body_required: bool = False

    # Response
    response_type: TypeInfo  # Success response type (usually 200/201)
    error_responses: Dict[int, TypeInfo] = Field(default_factory=dict)  # {404: TypeInfo(...)}

    # Metadata
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    deprecated: bool = False

    @property
    def method_name(self) -> str:
        """Generate Python method name from operation_id."""
        import re

        # Convert operationId to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", self.operation_id)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class ModelField(BaseModel):
    """Field in a data model (becomes a Pydantic model field)."""

    model_config = ConfigDict(frozen=False)

    name: str  # Python attribute name (sanitized, e.g. "id_")
    type_info: TypeInfo
    required: bool = True
    description: Optional[str] = None
    alias: Optional[str] = None  # JSON key when it differs from `name` (e.g. "id")


class Model(BaseModel):
    """
    Data model (becomes a Pydantic class).

    Examples:
        - User model with id, email, name
        - Product model with sku, price, description
    """

    model_config = ConfigDict(frozen=False)

    name: str  # Class name (e.g., "User", "Product")
    fields: List[ModelField]
    description: Optional[str] = None
    base_classes: List[str] = Field(default_factory=lambda: ["BaseModel"])

    # For nested models
    is_nested: bool = False

    # For enum models
    is_enum: bool = False
    enum_values: List[Any] = Field(default_factory=list)
    enum_type: str = "str"  # Base type: "str", "int", etc.


class AuthType(str, Enum):
    """Supported authentication types."""

    NONE = "none"
    BEARER = "bearer"  # Authorization: Bearer <token>
    API_KEY = "api_key"  # X-API-Key: <key>
    BASIC = "basic"  # Basic auth
    OAUTH2 = "oauth2"  # OAuth2 flows


class AuthConfig(BaseModel):
    """Authentication configuration."""

    model_config = ConfigDict(frozen=False)

    auth_type: AuthType = AuthType.NONE

    # For API key auth
    api_key_header: Optional[str] = None  # e.g., "X-API-Key"

    # For OAuth2
    oauth2_flows: Dict[str, Any] = Field(default_factory=dict)

    # Environment variable names
    token_env_var: Optional[str] = None  # e.g., "TOOL_REGISTRY_TOKEN"
    url_env_var: Optional[str] = None  # e.g., "TOOL_REGISTRY_URL"


class APISpec(BaseModel):
    """
    Complete API specification (Intermediate Representation).

    This is the unified format that the OpenAPI parser converts specs into.
    """

    model_config = ConfigDict(frozen=False)

    # Basic info
    name: str  # Service name (e.g., "tool_registry")
    title: str  # Human-readable title (e.g., "Tool Registry API")
    version: str  # API version (e.g., "1.0.0")
    description: Optional[str] = None

    # Base URL
    base_url: Optional[str] = None

    # Core API definition
    endpoints: List[Endpoint]
    models: List[Model]

    # Authentication
    auth_config: AuthConfig = Field(default_factory=AuthConfig)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    external_docs: Optional[str] = None

    # Original spec metadata
    original_spec_type: str = "openapi"
    original_spec_version: Optional[str] = None

    def get_model_by_name(self, name: str) -> Optional[Model]:
        """Find a model by name."""
        for model in self.models:
            if model.name == name:
                return model
        return None

    def get_endpoint_by_operation_id(self, operation_id: str) -> Optional[Endpoint]:
        """Find an endpoint by operation ID."""
        for endpoint in self.endpoints:
            if endpoint.operation_id == operation_id:
                return endpoint
        return None

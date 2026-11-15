# API Client Generator (apigen)

> **Modern, type-safe OpenAPI client generator**
>
> Generate comprehensive Pydantic v2 clients from OpenAPI 3.x specifications

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![uv](https://img.shields.io/badge/uv-managed-blue.svg)](https://docs.astral.sh/uv/)

---

## Overview

`apigen` is a next-generation OpenAPI client generator that produces type-safe, production-ready Python clients with:

✅ **Pydantic v2 Models** - Full type safety with modern Python typing
✅ **OpenAPI 3.x Support** - Handles OpenAPI 3.0, 3.1, and future versions
✅ **Async/Sync** - Native async with optional sync wrappers
✅ **Auto-Configuration** - Self-configuring from environment variables
✅ **Observability** - Built-in logging, metrics, and tracing
✅ **Production-Ready** - Retries, timeouts, error handling

### Why apigen?

**Compared to traditional generators:**

| Feature | apigen | openapi-python-client | Others |
|---------|--------|----------------------|--------|
| **Pydantic v2** | ✅ Native | ⚠️ Requires conversion | ❌ attrs/dataclasses |
| **OpenAPI 3.x** | ✅ Full support | ✅ Yes | ⚠️ Limited |
| **Type Safety** | ✅ 100% | ⚠️ Partial | ⚠️ Limited |
| **Auth** | ✅ Auto-configured | ⚠️ Manual | ⚠️ Manual |
| **Observability** | ✅ Built-in | ❌ None | ❌ None |
| **Future-Proof** | ✅ Extensible | ❌ Monolithic | ❌ Monolithic |

---

## Quick Start

### Installation

```bash
# Clone and install
cd api_client_generator
uv sync

# Verify installation
uv run apigen --version
```

### Generate Your First Client

1. **Add service to `.env`**

```bash
# .env
TOOL_REGISTRY_URL=https://api.example.com
TOOL_REGISTRY_TOKEN=your-secret-token
```

2. **Create configuration**

```toml
# apigen.toml
[generator]
auto_discover_from_env = true
output_base_dir = "clients"

[[services]]
name = "tool_registry"
spec_type = "openapi"
spec_location = "https://api.example.com/openapi.json"
```

3. **Generate client**

```bash
uv run apigen generate tool_registry
# ✓ Generated tool_registry at clients/tool_registry
```

4. **Use the client**

```python
from clients.tool_registry import get_client

# Auto-configured from TOOL_REGISTRY_URL and TOOL_REGISTRY_TOKEN
async with get_client() as client:
    tools = await client.get_tools()
    print(tools)  # Fully typed Pydantic models!
```

---

## Features

### 1. Type-Safe Pydantic v2 Models

All generated models use Pydantic v2 with full type safety:

```python
from clients.tool_registry.models import Tool
from pydantic import ValidationError

# Type-checked at runtime
tool = Tool(id=1, name="MyTool", version="1.0.0", tags=["automation"])

# Validation errors are detailed
try:
    Tool(id="invalid")  # Type error!
except ValidationError as e:
    print(e.errors())
```

### 2. OpenAPI 3.x Support

Full support for OpenAPI specifications:

```toml
[[services]]
name = "tool_registry"
spec_type = "openapi"
spec_location = "./openapi.json"

[[services]]
name = "worker_management"
spec_type = "openapi"
spec_location = "https://workers.example.com/openapi.json"

[[services]]
name = "legacy_api"
spec_type = "openapi"
spec_location = "./swagger.json"  # Also supports swagger.json
```

**Supported OpenAPI Versions:**

- ✅ **OpenAPI 3.0.x** (3.0.0, 3.0.1, 3.0.2, 3.0.3)
- ✅ **OpenAPI 3.1.x** (3.1.0)
- ✅ **Future versions** (extensible parser for upcoming OpenAPI releases)

### 3. Auto-Discovery from `.env`

No configuration needed - just add URLs to `.env`:

```bash
# .env
TOOL_REGISTRY_URL=https://api.example.com
REQUIREMENTS_MANAGEMENT_URL=https://requirements.example.com
WORKER_MANAGEMENT_URL=https://workers.example.com
```

```bash
# Discover all services
uv run apigen discover

# Generate all clients
uv run apigen generate --all
```

### 4. Authentication Built-In

Support for multiple auth strategies:

```python
# Bearer token (auto-configured from env)
from clients.tool_registry import get_client

client = get_client()  # Reads TOOL_REGISTRY_TOKEN from .env

# Manual configuration
from clients.tool_registry import ToolRegistryClient

client = ToolRegistryClient(
    base_url="https://api.example.com",
    auth_token="your-token",
    timeout=30,
    retries=3,
)
```

**Supported Auth Types:**
- Bearer Token
- API Key
- Basic Auth
- OAuth2 (coming soon)

### 5. Async & Sync Support

Native async with optional sync wrappers:

```python
# Async (default)
async with get_client() as client:
    result = await client.get_tools()

# Sync (wrapper)
from clients.tool_registry import ToolRegistryClientSync

with ToolRegistryClientSync.create() as client:
    result = client.get_tools()  # No await needed
```

### 6. Error Handling

Comprehensive error handling with typed exceptions:

```python
from clients.tool_registry import ToolRegistryClient
from clients.tool_registry.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    APIError,
)

try:
    tool = await client.get_tool(tool_id=123)
except NotFoundError:
    print("Tool not found")
except ValidationError as e:
    print(f"Validation failed: {e.errors}")
except AuthenticationError:
    print("Auth failed - check your token")
except APIError as e:
    print(f"API error: {e.status_code} - {e.detail}")
```

### 7. Observability

Built-in support for logging, metrics, and tracing:

```python
import logging
from clients.tool_registry import get_client

# Enable structured logging
logging.basicConfig(level=logging.INFO)

async with get_client() as client:
    # Automatically logs:
    # - Request method, URL, headers
    # - Response status, latency
    # - Errors with full context

    # Emits metrics:
    # - Request count
    # - Latency percentiles
    # - Error rates

    # Traces with correlation IDs
    result = await client.get_tools()
```

---

## CLI Reference

### `apigen generate`

Generate API client(s)

```bash
# Generate single client
apigen generate tool_registry

# Generate all clients
apigen generate --all

# Force regeneration (overwrite)
apigen generate tool_registry --force

# Use custom config
apigen generate --config apigen.toml
```

### `apigen discover`

Discover services from `.env`

```bash
apigen discover

# Output:
# Discovered Services:
# ============================================================
#   • tool_registry
#     Type: openapi
#     Spec: https://api.example.com/openapi.json
#
#   • worker_management
#     Type: openapi
#     Spec: https://workers.example.com/openapi.json
```

### `apigen validate`

Validate API specification

```bash
apigen validate tool_registry

# Output:
# ✓ tool_registry is valid
```

### `apigen migrate`

Migrate from legacy system

```bash
apigen migrate --legacy-dir ../open_api_management --output apigen.toml

# Output:
# ✓ Migration complete: apigen.toml
```

---

## Configuration

### File: `apigen.toml`

```toml
[generator]
# Auto-discover services from .env
auto_discover_from_env = true
env_file = ".env"

# Output directory
output_base_dir = "clients"

# Code formatting
use_black = true
use_isort = true

# Validation
strict_validation = true
fail_on_warnings = false

# Explicit service configuration (overrides auto-discovery)
[[services]]
name = "tool_registry"
spec_type = "openapi"
spec_location = "https://api.example.com/openapi.json"
package_name = "tool_registry"
auth_env_var = "TOOL_REGISTRY_TOKEN"

[[services]]
name = "custom_api"
spec_type = "openapi"
spec_location = "./specs/custom.yaml"
base_url = "https://custom.example.com"
timeout = 60
retries = 5
```

### Configuration in Python

```python
from pathlib import Path
from apigen.config import GeneratorConfig, ServiceConfig

config = GeneratorConfig(
    auto_discover_from_env=True,
    env_file=Path(".env"),
    output_base_dir=Path("clients"),
    use_black=True,
    services=[
        ServiceConfig(
            name="tool_registry",
            spec_type="openapi",
            spec_location="https://api.example.com/openapi.json",
        )
    ],
)

# Save to file
config.save(Path("apigen.toml"))
```

---

## Architecture

### Modular Architecture

`apigen` uses a modular architecture for maintainability:

```
┌─────────────────────────────────────────────┐
│              CLI Interface                   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Core Generator                      │
│  • Service Discovery (.env)                  │
│  • OpenAPI Parser (3.x)                      │
│  • Code Generator (Pydantic v2)              │
│  • Post-Processor (black, isort)             │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  OpenAPI Parser   │
         │  • 3.0.x support  │
         │  • 3.1.x support  │
         │  • Future-proof   │
         └───────────────────┘
```

### Intermediate Representation (IR)

OpenAPI specs are parsed into a clean IR for code generation:

```python
from apigen.core.ir import APISpec, Endpoint, Model

# OpenAPI spec → IR → Pydantic client
api_spec = APISpec(
    name="my_api",
    endpoints=[...],  # Parsed endpoints
    models=[...],  # Pydantic models
)
```

### Code Generation

Single Pydantic v2 generator for all specs:

```python
from apigen.core.code_gen import PydanticClientGenerator

generator = PydanticClientGenerator(
    output_dir=Path("clients"),
    template_dir=Path("templates"),
)

client_path = generator.generate(api_spec)
```

---

## Development

### Setup

```bash
# Clone repo
git clone <repo-url>
cd api_client_generator

# Install dependencies (includes test and lint tools)
uv sync --all-extras

# Run tests
uv run pytest -q

# Format code
uv run ruff format apigen tests
uv run ruff check --fix apigen tests
```

### Project Structure

```
api_client_generator/
├── apigen/                     # Main package
│   ├── cli.py                  # CLI interface
│   ├── config.py               # Configuration
│   ├── core/                   # Core logic
│   │   ├── generator.py
│   │   ├── ir.py               # Intermediate representation
│   │   ├── code_gen.py         # Code generator
│   │   └── discovery.py        # Service discovery
│   ├── plugins/                # Spec parsers
│   │   ├── base.py
│   │   └── openapi/
│   ├── templates/              # Jinja2 templates
│   └── utils/                  # Utilities
├── tests/                      # Tests
├── examples/                   # Examples
└── docs/                       # Documentation
```

### Extending OpenAPI Support

To add support for new OpenAPI features:

```python
from apigen.plugins.openapi.parser import OpenAPIParser
from apigen.core.ir import APISpec


class EnhancedOpenAPIParser(OpenAPIParser):
    """Extended parser for custom OpenAPI extensions"""

    def parse(self, spec) -> APISpec:
        # Call base parser
        api_spec = super().parse(spec)

        # Add custom extensions
        data = self.load_spec(spec)
        if "x-custom-extension" in data:
            # Handle custom extension
            pass

        return api_spec
```

---

## Migration from Legacy System

If you're migrating from `open_api_management`:

### 1. Run Migration Tool

```bash
uv run apigen migrate \
    --legacy-dir ../open_api_management \
    --output apigen.toml
```

### 2. Generate Clients

```bash
uv run apigen generate --all
```

### 3. Verify Imports

```python
# Old system
from clients.tool_registry import get_client

# New system (same import!)
from clients.tool_registry import get_client

# Everything works the same!
async with get_client() as client:
    result = await client.get_tools()
```

### 4. Archive Legacy System

```bash
mv open_api_management open_api_management.archived
```

---

## Roadmap

### Current (v0.1.0)

- ✅ Core architecture
- ✅ OpenAPI 3.x plugin
- ✅ Pydantic v2 code generation
- ✅ CLI interface
- ✅ Service discovery

### Next (v0.2.0)

- 🚧 OpenAPI 3.2+ support (when released)
- 🚧 Enhanced validation and error messages
- 🚧 Web UI for visualization
- 🚧 Custom OpenAPI extension support

### Future (v1.0.0)

- 🔮 Multi-language support (TypeScript, Go)
- 🔮 Cloud-hosted schema registry
- 🔮 Real-time spec synchronization
- 🔮 Performance optimizations for large specs

---

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests
4. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE). This distribution includes a [NOTICE](NOTICE) file.

## Licensing

This project is **not** licence-gated. There is no licence server, no activation step and no
runtime check: `apigen` runs entirely on your machine and never contacts a licensing service.
The Apache-2.0 licence is the only condition of use.

---

## Support

- **Documentation:** this README and the `examples/` directory
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

## Acknowledgments

Built as a modern, extensible alternative to hand-written OpenAPI clients.

**Key Technologies:**
- [Pydantic v2](https://docs.pydantic.dev/) - Type safety and validation
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine
- [Click](https://click.palletsprojects.com/) - CLI framework
- [uv](https://docs.astral.sh/uv/) - Package and environment management

---

**Made with ❤️ for modern Python development**

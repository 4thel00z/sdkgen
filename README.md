<div align="center">

<img src="https://raw.githubusercontent.com/4thel00z/sdkgen/master/logo.png" alt="SDKGen Logo" width="500" />

# SDKGen

### Multi-language SDK Generator from OpenAPI Specifications

_Type-safe • Async-first • Made for developers_

---

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

**[Quick Start](#-quick-start)** • **[Features](#-features)** • **[Documentation](docs/)** • **[Contributing](docs/CONTRIBUTING.md)**

---

</div>

## ✨ Features

* 🚀 **Multi-language support** - Python (TypeScript, Go, Rust planned)
* 🎯 **Type-safe** - Full type hints and TypedDict support
* ⚡ **Async-first** - Modern async patterns with httpx
* 🧩 **Complete OpenAPI 3.x** - $ref resolution, allOf/oneOf/anyOf, discriminators
* 📦 **Clean SDK structure** - Dataclass-based, resource-oriented
* 🔧 **Smart method naming** - Intelligent CRUD + RPC action detection
* 🌐 **Namespace support** - API versioning (v1, v2, beta)
* 🔐 **Auth built-in** - Bearer, API Key, OAuth2

## 📦 Installation

```bash
# Install from PyPI
pip install sdkgen

# Or using uv (recommended)
uv pip install sdkgen

# For development
git clone https://github.com/4thel00z/sdkgen
cd sdkgen
uv install
```

## ⚙️ Configuration

SDKGen works with any OpenAPI 3.x specification:

```bash
# From local file
sdkgen generate -i openapi.yaml -o ./my-sdk -l python

# From URL
sdkgen generate -i https://api.example.com/openapi.json -o ./my-sdk

# With custom package name
sdkgen generate -i spec.yaml -o ./sdk --package-name my_custom_sdk
```

## 🚀 Quick Start

### 1. Generate SDK from OpenAPI Spec

```bash
# Generate Python SDK
sdkgen generate \
  --input https://api.example.com/openapi.yaml \
  --output ./my-sdk \
  --language python \
  --package-name my_api_sdk
```

### 2. Use Generated SDK

```python
import asyncio
from my_sdk import Client

async def main():
    # Initialize client (reads from environment variables)
    client = Client(
        base_url="https://api.example.com",
        api_key="your-api-key"
    )

    # List resources with type-safe parameters
    users = await client.v1.users.list(page=0, size=10)
    print(f"Found {len(users)} users")

    # Create resource
    user = await client.v1.users.create(
        name="John Doe",
        email="john@example.com"
    )

    # Get by ID
    user = await client.v1.users.get(user_id="123")

    # Update
    updated = await client.v1.users.update(
        user_id="123",
        name="Jane Doe"
    )

    # Delete
    await client.v1.users.delete(user_id="123")

    # RPC-style actions
    pdf = await client.v1.files.download(file_id="abc")

asyncio.run(main())
```

## 🎯 Generated SDK Structure

SDKGen creates clean, maintainable SDK code:

```
my_sdk/
├── __init__.py
├── client.py          # Main Client dataclass
├── models.py          # TypedDict models + converters
├── utils.py           # Utility functions
└── resources/
    ├── __init__.py
    ├── v1.py          # V1 namespace
    ├── users.py       # Users resource
    └── files.py       # Files resource
```

## 🛡️ Type Safety

Generated SDKs use TypedDict for full type safety:

```python
from my_sdk.models import CreateUserInput, User

# Type-safe input (IDE autocomplete works!)
user_data: CreateUserInput = {
    "name": "John",
    "email": "john@example.com",
    "age": 30  # Optional field
}

user: User = await client.v1.users.create(**user_data)
```

## 📚 API Resources

### Supported OpenAPI Features

- ✅ $ref resolution (local and remote with caching)
- ✅ Schema composition (allOf, oneOf, anyOf)
- ✅ Discriminators for polymorphic types
- ✅ Path, query, header, cookie parameters
- ✅ Request bodies (JSON, form-data, multipart, binary)
- ✅ Multiple response types
- ✅ Authentication schemes (Bearer, API Key, OAuth2)
- ✅ Tags for resource grouping
- ✅ API versioning namespaces (v1, beta)
- ✅ Enums (string and integer)
- ✅ Nested resources
- ✅ Pagination patterns

### Method Naming Intelligence

SDKGen uses a 3-priority system for clean, intuitive method names:

1. **Clean operationId** - Extracts from OpenAPI operationId
2. **RPC-style actions** - Detects 35+ action verbs (download, activate, export, etc.)
3. **HTTP method + response** - Smart CRUD naming based on method and response type

Examples:
- `POST /api/v1/users` → `client.v1.users.create()`
- `GET /api/v1/users` (array) → `client.v1.users.list()`
- `GET /api/v1/users/{id}` (object) → `client.v1.users.get(id)`
- `GET /api/v1/files/{id}/download` → `client.v1.files.download(id)`
- `GET /health` → `client.health()`

## 🧪 Testing

```bash
# Validate OpenAPI spec
sdkgen validate -i openapi.yaml

# Show intermediate representation (debug)
sdkgen show-ir -i openapi.yaml

# Generate and test
sdkgen generate -i spec.yaml -o ./test-sdk
cd test-sdk && python -m py_compile **/*.py
```

## 🔧 Development

```bash
# See all available commands
make help

# Install dependencies
make dev

# Run all quality checks
make check

# Format code
make format

# Run linter
make lint

# Type check
make typecheck

# Test SDK generation
make test-sdk
```

## 📖 Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and patterns
- **[Usage Guide](docs/USAGE.md)** - Comprehensive usage documentation
- **[Agent Guidelines](docs/AGENT.md)** - For AI agents working on this project
- **[Contributing](docs/CONTRIBUTING.md)** - How to contribute
- **[API Reference](docs/API.md)** - Generated SDK API reference

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

```bash
# Quick start
make dev
make check
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the developer community**

[GitHub](https://github.com/4thel00z/sdkgen) • [Documentation](docs/) • [Issues](https://github.com/4thel00z/sdkgen/issues)

</div>

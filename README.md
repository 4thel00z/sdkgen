# SDKGen - OpenAPI SDK Generator

Multi-language SDK generator that creates type-safe, async-first SDKs from OpenAPI specifications.

## Quick Start

```bash
# Install
pip install sdkgen

# Generate Python SDK
sdkgen generate \
  --input https://api.example.com/openapi.yaml \
  --output ./my-sdk \
  --language python \
  --package-name my_api_sdk
```

## Features

- **Multi-language support**: Python (with TypeScript, Go, Rust planned)
- **Complete OpenAPI 3.x support**: $ref resolution, allOf/oneOf/anyOf, discriminators
- **Async-first**: Modern async patterns with httpx
- **Type-safe**: Full type hints and validation
- **Clean SDK style**: Dataclass-based, follows best practices

## Installation

```bash
pip install sdkgen
```

Or for development:

```bash
git clone https://github.com/yourusername/sdkgen
cd sdkgen
uv install
```

## Basic Usage

### Generate SDK

```bash
sdkgen generate -i spec.yaml -o ./sdk -l python
```

### Validate Spec

```bash
sdkgen validate -i spec.yaml
```

### Show IR (Debug)

```bash
sdkgen show-ir -i spec.yaml
```

## Using Generated SDKs

```python
from my_sdk import Client

# Initialize
client = Client(
    base_url="https://api.example.com",
    api_key="your-key"
)

# Use namespaced resources
users = await client.v1.users.list(page=0, size=10)
user = await client.v1.users.get(user_id="123")
await client.v1.users.create(name="John", email="john@example.com")
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and patterns
- **[Usage Guide](docs/USAGE.md)** - Comprehensive usage documentation
- **[Agent Guidelines](docs/AGENT.md)** - For AI agents working on this project
- **[Contributing](docs/CONTRIBUTING.md)** - How to contribute
- **[API Reference](docs/API.md)** - Generated SDK API reference

## Development

```bash
# Install with dev dependencies
uv install

# Run tests
pytest

# Format code
ruff format .

# Type check
mypy sdkgen

# Generate test SDK
uv run python -m sdkgen.cli generate \
  -i test_api/openapi.json \
  -o /tmp/test_sdk \
  -l python
```

## License

MIT

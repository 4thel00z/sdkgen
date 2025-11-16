# SDKGen - OpenAPI SDK Generator

Multi-language SDK generator that creates type-safe, async-first SDKs from OpenAPI specifications.

## Features

- **Multi-language support**: Python (with TypeScript, Go, Rust planned)
- **Complete OpenAPI 3.x support**: Including $ref resolution, allOf/oneOf/anyOf, discriminators
- **Async-first**: Generated SDKs use modern async patterns
- **Type-safe**: Full type hints and validation
- **OpenAPI SDK style**: Mirrors the OpenAI SDK architecture

## Installation

```bash
pip install sdkgen
```

## Usage

```bash
# Generate Python SDK from OpenAPI spec
sdkgen generate \
  --input https://api.example.com/openapi.yaml \
  --output ./my-sdk \
  --language python \
  --package-name my_api_sdk

# Validate OpenAPI spec
sdkgen validate --input openapi.yaml

# Show IR (for debugging)
sdkgen show-ir --input openapi.yaml
```

## Architecture

1. **OpenAPI Parser** → validates and resolves specs
2. **IR Builder** → creates language-agnostic intermediate representation
3. **Language Generators** → Python, TypeScript, Go, Rust

## Development

```bash
# Install dependencies
uv install --group dev .

# Run tests
pytest

# Format code
ruff format .

# Type check
mypy sdkgen
```


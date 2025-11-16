# SDKGen Usage Guide

## Installation

```bash
cd sdkgen
pip install -e .
```

## Quick Start

### 1. Generate SDK from OpenAPI Spec

```bash
sdkgen generate \
  --input https://api.example.com/openapi.yaml \
  --output ./my-sdk \
  --language python \
  --package-name my_api_sdk
```

### 2. Validate OpenAPI Spec

```bash
sdkgen validate --input openapi.yaml
```

### 3. Show Intermediate Representation (IR)

```bash
# Output to stdout
sdkgen show-ir --input openapi.yaml

# Save to file
sdkgen show-ir --input openapi.yaml --output ir.json
```

## CLI Commands

### `generate`

Generate SDK from OpenAPI specification.

**Options:**
- `--input, -i`: Path or URL to OpenAPI spec (required)
- `--output, -o`: Output directory for SDK (required)
- `--language, -l`: Target language (python, typescript, go, rust) [default: python]
- `--package-name, -n`: Package name (default: from OpenAPI title)

**Examples:**

```bash
# From local file
sdkgen generate -i openapi.yaml -o ./sdk -l python

# From URL
sdkgen generate -i https://api.com/spec.yaml -o ./sdk

# Custom package name
sdkgen generate -i spec.yaml -o ./sdk --package-name my_custom_sdk
```

### `validate`

Validate OpenAPI specification structure.

**Options:**
- `--input, -i`: Path or URL to OpenAPI spec (required)

**Example:**

```bash
sdkgen validate -i openapi.yaml
```

Output:
```
✓ Valid OpenAPI specification!
  Version: 3.1.0
  Title: My API
  Paths: 25
  Schemas: 15
```

### `show-ir`

Display intermediate representation of OpenAPI spec.

**Options:**
- `--input, -i`: Path or URL to OpenAPI spec (required)
- `--output, -o`: Output file for IR JSON (optional)

**Example:**

```bash
# Print to console
sdkgen show-ir -i openapi.yaml

# Save to file
sdkgen show-ir -i openapi.yaml -o ir.json
```

## Generated SDK Structure (Python)

After running `sdkgen generate`, you'll get:

```
my_sdk/
├── README.md
├── pyproject.toml
└── my_sdk/
    ├── __init__.py
    ├── client.py          # Client dataclass with auth
    ├── models.py          # TypedDict models + converters
    ├── utils.py           # Utility functions
    └── resources/
        ├── __init__.py
        ├── v1.py          # V1 namespace
        └── users.py       # Resource dataclasses
```

## Using Generated SDK

```python
from my_sdk import Client

# Initialize client
client = Client(
    base_url="https://api.example.com",
    api_key="your-api-key"
)

# Use namespaced resources
users = await client.v1.users.list(page=0, size=10)

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
```

## Advanced Usage

### Environment Variables

Generated SDKs support environment variables:

```bash
export BASE_URL="https://api.example.com"
export API_KEY="your-secret-key"
```

```python
# No need to pass credentials
client = Client()
```

### Custom Client Options

```python
# Override timeout
client = Client(timeout=120.0)

# Custom headers
client = Client(headers={"X-Custom": "value"})

# Create new client with different options
client2 = client.with_options(timeout=60.0)

# Create client with namespace
v1_client = client.with_namespace("/api/v1")
```

### Binary Responses

For endpoints returning binary data:

```python
# Download file
pdf_bytes = await client.v1.files.download(file_id="123")

with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Typed Request Bodies

Python SDKs use `Unpack[TypedDict]` for flexibility:

```python
from my_sdk.models import CreateUserInput

# TypedDict provides autocomplete and type checking
user_data: CreateUserInput = {
    "name": "John",
    "email": "john@example.com",
    "age": 30  # Optional field
}

user = await client.v1.users.create(**user_data)
```

## OpenAPI Features Supported

### ✅ Complete Support

- **$ref Resolution**: Local and remote (with caching)
- **Schema Composition**: allOf, oneOf, anyOf
- **Discriminators**: Polymorphic types
- **Path Parameters**: Template variables
- **Query Parameters**: All types and formats
- **Request Bodies**: JSON, form-data, binary
- **Responses**: Multiple status codes
- **Authentication**: Bearer, API Key, OAuth2
- **Tags**: Resource grouping
- **Namespaces**: Versioning (v1, beta)
- **Enums**: String and integer enums
- **Nested Resources**: Auto-detection
- **Pagination**: Offset, cursor, page-based
- **Validation**: min, max, pattern, format

### Language-Specific Features

**Python:**
- TypedDict models (not Pydantic)
- Dataclass Client and Resources
- Async-first with httpx
- snake_case Python API
- camelCase HTTP API
- Auto converters
- Full type hints
- NotRequired for optional fields
- Unpack[TypedDict] for kwargs

## Troubleshooting

### Issue: "Invalid OpenAPI specification"

**Solution:** Validate your spec first:
```bash
sdkgen validate -i your-spec.yaml
```

### Issue: "Reference not found"

**Solution:** Ensure external $refs are accessible. For local files, use relative paths.

### Issue: "Generated code has type errors"

**Solution:** Run mypy on generated code:
```bash
cd my_sdk
mypy my_sdk
```

### Issue: "Package name conflicts"

**Solution:** Use `--package-name` to specify custom name:
```bash
sdkgen generate -i spec.yaml -o ./sdk --package-name unique_name
```

## Examples

### Minimal OpenAPI Spec

```yaml
openapi: 3.1.0
info:
  title: Simple API
  version: 1.0.0
servers:
  - url: https://api.example.com
paths:
  /users:
    get:
      tags: [users]
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      required: [id, name]
      properties:
        id:
          type: string
        name:
          type: string
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
```

Generate SDK:
```bash
sdkgen generate -i simple.yaml -o ./simple-sdk -l python
```

### Complex Example with Nested Resources

```yaml
openapi: 3.1.0
# ... (see examples/complex-api.yaml)
```

## Next Steps

1. **Customize Generated SDK**: Edit generated code as needed
2. **Add Tests**: Write tests for your SDK usage
3. **Publish**: Package and publish to PyPI
4. **Documentation**: Add usage examples to README

## Contributing

To add support for a new language:

1. Create `sdkgen/generators/{language}/`
2. Implement generators as dataclasses
3. Add to CLI language options
4. Add tests

See `ARCHITECTURE.md` for details.

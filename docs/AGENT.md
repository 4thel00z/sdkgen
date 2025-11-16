# Agent Guidelines - SDKGen

This document provides comprehensive guidelines for AI agents working on the SDKGen project.

## Project Overview

SDKGen is a multi-language SDK generator that converts OpenAPI 3.x specifications into type-safe, async-first SDKs. Currently supports Python with TypeScript, Go, and Rust planned.

## Project Structure

```
sdkgen/
├── sdkgen/
│   ├── analyzers/          # Pattern detection services
│   │   ├── endpoint_analyzer.py    # Groups operations into resources
│   │   ├── namespace_analyzer.py   # Detects API versioning (v1, beta)
│   │   ├── naming_analyzer.py      # Detects snake_case vs camelCase
│   │   └── nested_detector.py      # Finds nested resources
│   ├── core/               # Application layer
│   │   ├── ir.py                   # Domain models (IR dataclasses)
│   │   ├── ir_builder.py           # Orchestrates IR building
│   │   ├── parser.py               # OpenAPI parser
│   │   ├── resolver.py             # $ref resolver
│   │   ├── schema_analyzer.py      # allOf/oneOf/anyOf handler
│   │   └── type_mapper.py          # OpenAPI → IR type mapping
│   ├── generators/         # Output adapters
│   │   └── python/
│   │       ├── client_gen.py       # Generates Client class
│   │       ├── models_gen.py       # Generates TypedDict models
│   │       ├── enums_gen.py        # Generates Enum classes
│   │       ├── resources_gen.py    # Generates resource classes
│   │       ├── namespace_gen.py    # Generates namespace aggregators
│   │       ├── converters_gen.py   # Generates converters
│   │       ├── utils_gen.py        # Generates utilities
│   │       └── generator.py        # Main coordinator
│   ├── utils/              # Shared utilities
│   │   ├── case_converter.py       # snake_case ↔ camelCase
│   │   ├── name_sanitizer.py       # Sanitizes identifiers
│   │   └── http_cache.py           # Caches HTTP requests
│   └── cli.py              # CLI interface
├── tests/                  # Test suite
│   ├── test_parser.py
│   ├── test_ir_builder.py
│   ├── test_python_generator.py
│   └── fixtures/
│       └── openapi_specs/
├── test_api/              # FastAPI test server
│   └── main.py            # Comprehensive test API
└── docs/                  # Documentation
    ├── AGENT.md          # This file
    ├── ARCHITECTURE.md   # Architecture details
    ├── USAGE.md         # Usage guide
    ├── CONTRIBUTING.md  # Contribution guide
    └── API.md           # API reference
```

## Architecture Principles

### Hexagonal/DDD Architecture

- **Domain Layer**: `core/ir.py` - Pure dataclasses, no external dependencies
- **Application Layer**: `core/` - Business logic, orchestration
- **Infrastructure Layer**: `analyzers/`, `generators/`, `utils/` - All adapters are dataclasses

### Key Patterns

1. **No Singletons**: Use dataclasses with `field(default_factory=...)`
2. **Pure Functional**: No mutation, no variable reassignment
3. **Async-First**: All I/O operations use async/await
4. **Type Safety**: Type hints everywhere, validated with mypy

## Coding Guidelines

### Python Style

```python
# ✅ DO: Use dataclasses with field defaults
@dataclass
class IRBuilder:
    endpoint_analyzer: EndpointAnalyzer = field(default_factory=EndpointAnalyzer)

# ❌ DON'T: Use useless __init__ methods
@dataclass
class IRBuilder:
    def __init__(self):
        self.endpoint_analyzer = EndpointAnalyzer()
```

### Required Imports

```python
# Always use for forward references
from __future__ import annotations

# Dataclasses
from dataclasses import dataclass, field

# Type hints
from typing import Any
```

### Naming Conventions

- **Python code**: `snake_case` for variables, functions, methods
- **Classes**: `PascalCase`
- **API fields**: `camelCase` (in OpenAPI specs)
- **No underscore prefixes**: No `_private_var` - use descriptive names

### File Operations

```python
# ✅ DO: Use pathlib
from pathlib import Path
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)

# ❌ DON'T: Use os.path
import os
os.makedirs("output", exist_ok=True)
```

### Method Naming (Generated SDKs)

The 3-priority system for naming generated methods:

1. **Clean operationId** - If present in OpenAPI spec
2. **RPC-style actions** - For paths like `/resource/{id}/action`, use action name (download, activate, export, etc.)
3. **HTTP method + response schema**:
   - `GET` + array response → `list()`
   - `GET` + object + path param → `get()`
   - `GET` + object + no param → use path name (e.g., `health()`, `status()`)
   - `POST` → `create()`
   - `PUT`/`PATCH` → `update()`
   - `DELETE` → `delete()`

**35+ RPC Action Words:**
download, upload, export, import, activate, deactivate, enable, disable, publish, unpublish, archive, unarchive, approve, reject, cancel, complete, submit, confirm, verify, validate, execute, trigger, run, start, stop, pause, resume, retry, restart, refresh, sync, clone, duplicate, copy, resend, reprocess, summary, status, health, me, current

## Common Tasks & Workflows

### Task 1: Add Support for New OpenAPI Feature

1. **Update IR** (`core/ir.py`):
   ```python
   @dataclass
   class NewFeature:
       name: str
       description: str | None = None
   ```

2. **Update IRBuilder** (`core/ir_builder.py`):
   ```python
   def build_new_feature(self, spec: dict[str, Any]) -> NewFeature:
       return NewFeature(name=spec["name"])
   ```

3. **Update Generators** (`generators/python/*.py`):
   ```python
   def generate_new_feature(self, feature: NewFeature) -> str:
       return f"# {feature.name}"
   ```

4. **Add Tests**:
   ```python
   def test_new_feature():
       spec = {"name": "test"}
       feature = builder.build_new_feature(spec)
       assert feature.name == "test"
   ```

### Task 2: Add New Analyzer

1. **Create Analyzer** (`analyzers/new_analyzer.py`):
   ```python
   from dataclasses import dataclass
   from typing import Any

   @dataclass
   class NewAnalyzer:
       def analyze(self, spec: dict[str, Any]) -> dict[str, Any]:
           # Analysis logic here
           return {}
   ```

2. **Integrate into IRBuilder**:
   ```python
   @dataclass
   class IRBuilder:
       new_analyzer: NewAnalyzer = field(default_factory=NewAnalyzer)
   ```

3. **Add Tests**

### Task 3: Fix Generated Code Issue

1. **Identify Generator**: Find which generator creates the problematic code
2. **Update Template/Logic**: Fix in `generators/python/*.py`
3. **Test**: Generate SDK from test_api and verify

### Task 4: Add Language Support

1. **Create Directory**: `generators/{language}/`
2. **Implement Generators**: Models, Client, Resources, etc. (all dataclasses)
3. **Create Coordinator**: Main generator class
4. **Update CLI**: Add language option
5. **Add Tests**

## Testing Approach

### Unit Tests

Test individual components:

```bash
pytest tests/test_parser.py -v
pytest tests/test_ir_builder.py -v
```

### Integration Tests

Test full pipeline:

```bash
pytest tests/test_python_generator.py -v
```

### Real-World Test

Use the test API:

```bash
# Terminal 1: Start test API
cd test_api && uv run uvicorn main:app

# Terminal 2: Generate SDK
uv run python -m sdkgen.cli generate \
  -i http://127.0.0.1:8000/openapi.json \
  -o /tmp/test_sdk \
  -l python

# Verify generated code
cd /tmp/test_sdk
python -m py_compile test_sdk/**/*.py
```

### Test Coverage Areas

- OpenAPI parsing and validation
- $ref resolution (local and remote)
- Schema composition (allOf/oneOf/anyOf)
- Type mapping
- Method naming
- Parameter extraction
- Generated code syntax
- Generated code type safety

## Where to Find Things

### Core Domain Models
→ `core/ir.py`

### OpenAPI Parsing
→ `core/parser.py`

### $ref Resolution
→ `core/resolver.py`

### Type Mapping
→ `core/type_mapper.py`

### Method Naming Logic
→ `analyzers/endpoint_analyzer.py` → `infer_operation_name()`

### Resource Grouping
→ `analyzers/endpoint_analyzer.py` → `group_by_tags()`

### Namespace Detection
→ `analyzers/namespace_analyzer.py`

### Python Code Generation
→ `generators/python/`

### CLI Commands
→ `cli.py`

### Test Fixtures
→ `tests/fixtures/openapi_specs/`

### Example API
→ `test_api/main.py` (comprehensive FastAPI with all edge cases)

## Development Commands

All development commands are available through the Makefile:

```bash
# See all available commands
make help

# Install dependencies
make dev

# Format code
make format

# Lint
make lint

# Type check
make typecheck

# Run tests
make test

# Generate and verify SDK from test API
make test-sdk

# Run all quality checks
make check
```

## Common Pitfalls to Avoid

### ❌ Don't: Use useless __init__ methods
```python
@dataclass
class Builder:
    def __init__(self):
        self.analyzer = Analyzer()  # WRONG!
```

### ✅ Do: Use field defaults
```python
@dataclass
class Builder:
    analyzer: Analyzer = field(default_factory=Analyzer)
```

### ❌ Don't: Nest main logic deeply
```python
def process_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if spec:
        if spec.get("paths"):
            if spec["paths"].get("/users"):
                # Main logic buried 3 levels deep
                return process_users(spec["paths"]["/users"])
    return {}
```

### ✅ Do: Use guardian pattern (early returns)
```python
def process_spec(spec: dict[str, Any]) -> dict[str, Any]:
    # Guard clauses first
    if not spec:
        return {}
    if not spec.get("paths"):
        return {}
    if not spec["paths"].get("/users"):
        return {}

    # Main logic at lowest indentation
    return process_users(spec["paths"]["/users"])
```

### ❌ Don't: Variable reassignment (imperative)
```python
lines = []
lines.append("foo")
lines.append("bar")
return "\n".join(lines)
```

### ✅ Do: Pure functional
```python
return "\n".join([
    "foo",
    "bar",
])
```

### ❌ Don't: Mix return types
```python
def generate(self) -> str | list[str]:  # WRONG!
    ...
```

### ✅ Do: Consistent return types
```python
def generate(self) -> str:
    return "\n".join(lines)
```

### ❌ Don't: Forget type hints
```python
def process(data):  # WRONG!
    return data
```

### ✅ Do: Always add type hints
```python
def process(data: dict[str, Any]) -> dict[str, Any]:
    return data
```

### ❌ Don't: Game the linter
```python
def complex_function():  # noqa: PLR0911
    # WRONG! Suppressing warnings instead of fixing
    ...
```

### ✅ Do: Fix issues or configure globally
```python
# Option 1: Fix the actual issue
def complex_function():
    # Refactor to reduce complexity
    ...

# Option 2: If rule is not applicable, blacklist in pyproject.toml
# [tool.ruff.lint]
# ignore = ["PLR0911"]
```

## Debugging Tips

### View Generated IR

```bash
sdkgen show-ir -i spec.yaml -o ir.json
```

### Check Generated Code Syntax

```bash
python -m py_compile generated_file.py
```

### Use Test API for Development

The `test_api/` contains a comprehensive FastAPI application with:
- Multiple namespaces (v1, v2, beta)
- All HTTP methods
- Batch operations
- File uploads
- Nested resources
- Pagination
- Complex response types

### Print Debug Info

Add temporary logging:

```python
import json
print(json.dumps(data, indent=2))
```

## Quick Reference

### Dataclass Pattern
```python
from dataclasses import dataclass, field

@dataclass
class Component:
    dependency: Dependency = field(default_factory=Dependency)

    def method(self) -> str:
        return "result"
```

### Type Hints
```python
from typing import Any

def func(
    required: str,
    optional: str | None = None,
    union: str | int = "default",
    collection: list[str] = field(default_factory=list),
) -> dict[str, Any]:
    return {}
```

### Functional Pattern
```python
return "\n".join([
    "line 1",
    "line 2",
    "line 3",
])
```

### Guardian Pattern (Early Returns)
```python
def process(data: dict[str, Any]) -> str | None:
    # Guard clauses first - handle edge cases
    if not data:
        return None
    if not data.get("required_field"):
        return None

    # Main logic at lowest indentation
    return perform_processing(data)
```

## Plan-Agent Cycle Workflow

After completing any plan implementation cycle, **always** follow this workflow:

### 1. Test All Changes

```bash
# Run all quality checks
make check

# Or run individually
make lint
make typecheck
make test-sdk
make test
```

### 2. Commit Changes

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: add guardian pattern and refactor nested conditionals"

# Push (when ready)
git push origin branch-name
```

### Key Principles

- **Never skip testing**: Always verify changes work before committing
- **Test end-to-end**: Generate actual SDK and verify it compiles
- **Atomic commits**: Each plan cycle = one focused commit
- **Clear messages**: Describe what changed and why

## Questions?

- Check `docs/ARCHITECTURE.md` for architecture details
- Check `docs/USAGE.md` for usage examples
- Check `docs/API.md` for API reference
- Check tests for code examples
- Open a discussion on GitHub

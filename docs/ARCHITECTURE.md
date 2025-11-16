# SDKGen Architecture

## Overview

SDKGen is a multi-language SDK generator built with hexagonal/DDD architecture that converts OpenAPI specifications into type-safe, async-first SDKs.

## Architecture Layers

### Domain Layer (`core/ir.py`)
- **IR (Intermediate Representation)**: Language-agnostic data structures representing SDK components
- All domain models are dataclasses
- No external dependencies

### Application Layer (`core/`)
- **Parser**: Validates and loads OpenAPI specs
- **Resolver**: Resolves $ref (local and remote)
- **SchemaAnalyzer**: Handles allOf/oneOf/anyOf compositions
- **TypeMapper**: Maps OpenAPI types to IR types
- **IRBuilder**: Orchestrates building complete IR from spec

### Infrastructure Layer (Adapters)
All adapters are dataclasses (per hexagonal architecture):

#### Input Adapters
- **OpenAPIParser**: Reads specs from files/URLs
- **ReferenceResolver**: Fetches and caches external refs
- **HTTPCache**: Caches remote resources

#### Output Adapters (Code Generators)
- **PythonModelsGenerator**: Generates TypedDict models
- **PythonEnumsGenerator**: Generates Enum classes
- **PythonConvertersGenerator**: Generates snake↔camel converters
- **PythonClientGenerator**: Generates Client dataclass
- **PythonResourcesGenerator**: Generates resource dataclasses
- **PythonUtilsGenerator**: Generates utility functions
- **PythonGenerator**: Main coordinator

### Analyzers (`analyzers/`)
Pattern detection services (all dataclasses):
- **EndpointAnalyzer**: Groups operations into resources
- **NamespaceAnalyzer**: Detects API versioning (v1, beta)
- **NamingAnalyzer**: Detects snake_case vs camelCase patterns
- **NestedDetector**: Finds nested resource patterns

## Data Flow

```
OpenAPI Spec (YAML/JSON)
    ↓
OpenAPIParser
    ↓
ReferenceResolver (resolve $refs)
    ↓
SchemaAnalyzer + TypeMapper + Analyzers
    ↓
IRBuilder
    ↓
SDKProject (IR)
    ↓
Language Generator (Python, TS, Go, Rust)
    ↓
Generated SDK Code
```

## Key Patterns

### 1. Hexagonal Architecture
- Domain at center (IR dataclasses)
- Application layer orchestrates
- Infrastructure adapters are ports
- No singletons

### 2. Dataclass-Based Design
- All services/adapters are dataclasses
- Immutable where possible
- Explicit dependencies via constructor

### 3. Async-First
- All I/O operations are async
- httpx for HTTP
- Supports concurrent operations

### 4. Type Safety
- Full type hints throughout
- TypedDict for data structures
- mypy validation

## Generated SDK Style (Python)

### Matches pharia_data_sdk:
- Client as dataclass
- Resources as dataclasses
- TypedDict models (not Pydantic)
- snake_case Python API, camelCase HTTP API
- Converter functions for case conversion
- Async httpx-based requests
- Namespace properties (v1, beta)
- `Unpack[TypedDict]` for flexible kwargs

### Example Generated Structure:
```
my_sdk/
├── __init__.py
├── client.py        # Client dataclass
├── models.py        # TypedDict definitions + converters
├── utils.py         # Case conversion helpers
└── resources/
    ├── __init__.py
    ├── users.py     # Users resource dataclass
    └── products.py  # Products resource dataclass
```

## Extension Points

### Adding New Language
1. Create `generators/{language}/` directory
2. Implement language-specific generators (all dataclasses)
3. Create main generator coordinator
4. Add to CLI language options

### Adding New Analyzer
1. Create dataclass in `analyzers/`
2. Implement analysis logic
3. Integrate into IRBuilder

### Adding New IR Feature
1. Add dataclass to `core/ir.py`
2. Update IRBuilder to populate it
3. Update generators to consume it

## Testing Strategy

1. **Unit Tests**: Each analyzer/generator independently
2. **Integration Tests**: Full OpenAPI → IR → Code
3. **Validation Tests**: Compare generated SDK to reference (pharia_data_sdk)

## Dependencies

**Core:**
- httpx: Async HTTP
- pyyaml: YAML parsing
- pydantic: OpenAPI validation
- click: CLI
- jsonref: $ref resolution

**Dev:**
- pytest + pytest-asyncio: Testing
- ruff: Linting & formatting
- mypy: Type checking

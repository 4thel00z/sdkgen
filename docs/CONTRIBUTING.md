# Contributing to SDKGen

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install dependencies: `uv install`
4. Create a feature branch: `git checkout -b feature/your-feature`

## Development Setup

All commands are available via the Makefile:

```bash
# See all available commands
make help

# Install with dev dependencies
make dev

# Run tests
make test

# Format code
make format

# Lint
make lint

# Type check
make typecheck

# Run all quality checks
make check
```

## Coding Guidelines

### Architecture

- Use hexagonal/DDD architecture
- All infrastructure adapters must be dataclasses
- No dependency injection singletons
- Streamlined functional code over imperative

### Python Style

- No `__future__` imports (except `annotations`)
- No `abc` package
- Absolute imports only
- Use pathlib (`Path`) for all file operations (never `os.path`)
- No underscore prefixes for variables
- TypedDict for data models
- Dataclasses for services/adapters
- Async-first with httpx

### Code Quality

- Target Python 3.12+
- Type hints everywhere
- snake_case for Python, camelCase for API
- No useless wrappers

### Method Naming (Generated SDKs)

Follow the 3-priority system:

1. **Clean operationId**: If present, extract method name
2. **RPC-style actions**: For paths like `/resource/{id}/action`, use action name
3. **HTTP method + response schema**:
   - GET + array response → `list()`
   - GET + object + path param → `get()`
   - GET + object + no param → use path name (e.g., `health()`)
   - POST → `create()`
   - PUT/PATCH → `update()`
   - DELETE → `delete()`

## Testing

### Unit Tests

Test individual components in isolation:

```bash
pytest tests/test_parser.py
pytest tests/test_ir_builder.py
```

### Integration Tests

Test full generation pipeline:

```bash
pytest tests/test_python_generator.py
```

### Real-World Test

Generate SDK from test API:

```bash
# Start test API
cd test_api && uv run uvicorn main:app

# Generate SDK
uv run python -m sdkgen.cli generate \
  -i http://127.0.0.1:8000/openapi.json \
  -o /tmp/test_sdk \
  -l python
```

## Adding Features

### Adding a New Analyzer

1. Create dataclass in `sdkgen/analyzers/`
2. Implement analysis logic
3. Add tests
4. Integrate into `IRBuilder`

### Adding Language Support

1. Create `sdkgen/generators/{language}/` directory
2. Implement generator classes (all dataclasses):
   - Client generator
   - Models generator
   - Resources generator
   - etc.
3. Create main coordinator
4. Add to CLI language options
5. Add tests

### Adding IR Features

1. Add dataclass to `sdkgen/core/ir.py`
2. Update `IRBuilder` to populate it
3. Update generators to consume it
4. Add tests

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Follow coding guidelines
4. Write clear commit messages
5. Create PR with description of changes

## Code Review Criteria

- Follows architecture patterns
- Has adequate test coverage
- Type hints present
- Documentation updated
- No breaking changes (or clearly marked)
- Code is simple and maintainable

## Questions?

Open an issue or discussion on GitHub.

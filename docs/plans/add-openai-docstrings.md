# Plan: Add OpenAI-Style Docstrings to All Functions

**Created**: 2025-11-17 00:15:30  
**Status**: Ready for implementation  
**Estimated Effort**: 4-6 hours (incremental)

---

## Goal

Add comprehensive, OpenAI-style docstrings to all 127 functions across 22 Python files.

## Docstring Format

```python
def function_name(param1: str, param2: int = 0) -> dict[str, Any]:
    """One-line summary of what the function does.

    Detailed explanation of the function's purpose, behavior,
    and any important implementation details.

    Args:
        param1: Description of what param1 represents
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of what the function returns

    Raises:
        ValueError: When param1 is invalid
        TypeError: When param2 is wrong type

    Example:
        >>> result = function_name("test", 5)
        >>> print(result)
        {'status': 'success'}
    """
    # Implementation
```

## Files to Document (22 files, 127 functions)

### Priority 1: Utils (3 files, ~15 functions)
These are the simplest, most reusable functions.

**utils/case_converter.py** (~5 functions)
- to_snake_case()
- to_camel_case()
- to_pascal_case()
- detect_naming_convention()

**utils/name_sanitizer.py** (~5 functions)
- sanitize_python_name()
- sanitize_package_name()
- sanitize_class_name()
- sanitize_enum_member_name()

**utils/http_cache.py** (~5 functions)
- __init__()
- get_cache_path()
- fetch()
- clear()
- clear_url()

### Priority 2: Analyzers (4 files, ~30 functions)

**analyzers/endpoint_analyzer.py** (~10 functions)
- group_by_tags()
- extract_resource_from_path()
- detect_path_prefix()
- requires_resource_id()
- response_is_array()
- clean_operation_id()
- infer_operation_name()

**analyzers/namespace_analyzer.py** (~6 functions)
- detect_namespaces()
- extract_namespace_from_path()
- extract_namespace_from_url()
- group_paths_by_namespace()

**analyzers/naming_analyzer.py** (~8 functions)
- detect_field_naming()
- detect_parameter_naming()
- analyze_naming_patterns()
- etc.

**analyzers/nested_detector.py** (~6 functions)
- detect_nested_resources()
- extract_nested_from_operation_id()
- get_nested_property_name()
- should_create_nested_resource()

### Priority 3: Core (6 files, ~50 functions)

**core/ir.py** (~40 dataclasses)
- Add class-level docstrings to all dataclasses
- Document each field's purpose

**core/ir_builder.py** (~20 functions)
- build()
- build_metadata()
- build_auth_config()
- build_type_registry()
- build_resources()
- build_operation()
- extract_path_params()
- extract_query_params()
- extract_response_type()
- extract_request_body_params()
- etc.

**core/parser.py** (~8 functions)
- parse()
- load_spec()
- load_from_url()
- load_from_file()
- validate_spec()

**core/resolver.py** (~6 functions)
- resolve()
- resolve_node()
- resolve_reference()
- load_external_spec()

**core/schema_analyzer.py** (~8 functions)
- analyze_composition()
- build_composition()
- extract_discriminator()
- merge_all_of_schemas()

**core/type_mapper.py** (~8 functions)
- map_schema()
- extract_validation_rules()
- get_python_type_hint()

### Priority 4: Generators (8 files, ~25 functions)

**generators/python/generator.py** (~5 functions)
- generate()
- generate_client()
- generate_models()
- generate_resources()

**generators/python/client_gen.py** (~8 functions)
- generate()
- generate_imports()
- generate_client_class()
- generate_namespace_property()
- generate_utility_method()
- generate_request_method()

**generators/python/resources_gen.py** (~10 functions)
- generate()
- generate_resource()
- generate_operation()
- build_request_payload()
- build_query_params_dict()

**generators/python/models_gen.py** (~5 functions)
- generate()
- generate_model()
- generate_imports()

**generators/python/namespace_gen.py** (~2 functions)
- generate()

**generators/python/enums_gen.py** (~3 functions)
- generate()
- generate_enum()

**generators/python/converters_gen.py** (~3 functions)
- generate()
- generate_converter()

**generators/python/utils_gen.py** (~2 functions)
- generate()

### Priority 5: CLI (1 file, ~5 functions)

**cli.py**
- main()
- generate_command()
- validate_command()
- show_ir_command()

---

## Implementation Strategy

### Phase 1: Utils (1 hour)
Document all utility functions with examples.

### Phase 2: Analyzers (1.5 hours)
Document pattern detection logic with algorithm explanations.

### Phase 3: Core (2 hours)
Most complex - document IR building, parsing, resolution.

### Phase 4: Generators (1.5 hours)
Document code generation templates and logic.

### Phase 5: CLI (30 minutes)
Document CLI interface and commands.

---

## Useless Wrappers Identified

### 1. create_resource_name() - REMOVED ✅
**Was**: Wrapper around sanitize_class_name()  
**Status**: Already removed in this session

### 2. build_params_dict() in resources_gen.py
**Current**: Returns None, params built inline  
**Action**: Already just a placeholder, keep for now

---

## Documentation Standards

### Required Elements

**All public functions must have**:
1. One-line summary
2. Detailed description (if complex)
3. Args section
4. Returns section
5. Raises section (if applicable)

**Complex functions should include**:
6. Example section showing usage

### Examples to Follow

```python
def detect_namespaces(self, spec: dict[str, Any]) -> list[Namespace]:
    """Detect API versioning namespaces from OpenAPI specification.

    Analyzes paths and server URLs to identify version patterns like
    v1, v2, beta, alpha. Creates Namespace objects for organizing
    resources by API version.

    Args:
        spec: Complete OpenAPI 3.x specification dictionary

    Returns:
        List of detected Namespace objects, each containing:
        - name: Version identifier (v1, v2, beta)
        - path_prefix: URL prefix for the namespace
        - resources: Empty list (populated later)

    Example:
        >>> analyzer = NamespaceAnalyzer()
        >>> spec = {"paths": {"/api/v1/users": {...}}}
        >>> namespaces = analyzer.detect_namespaces(spec)
        >>> print(namespaces[0].name)
        'v1'
    """
    # Implementation
```

---

## Testing After Documentation

After each phase, run:

```bash
make check        # Verify code still works
make test-e2e     # Ensure SDK generation works
```

---

## Commit Strategy

Commit after each priority group:

```bash
git add .
git commit -m "docs: add comprehensive docstrings to utils/"
git commit -m "docs: add comprehensive docstrings to analyzers/"
git commit -m "docs: add comprehensive docstrings to core/"
git commit -m "docs: add comprehensive docstrings to generators/"
git commit -m "docs: add comprehensive docstrings to cli"
```

---

## Success Criteria

✅ All 127 functions have comprehensive docstrings  
✅ OpenAI style consistently applied  
✅ Examples included for complex functions  
✅ All tests passing  
✅ make check passes  
✅ SDK generation works

---

## Notes

- This is incremental work, can be done over multiple sessions
- Focus on clarity and usefulness
- Include examples for non-obvious functions
- Keep existing good docstrings, enhance if needed
- Don't add docstrings to private/internal functions (those with leading _)


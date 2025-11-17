"""Name sanitization for valid Python identifiers."""

import keyword
import re

from sdkgen.utils.case_converter import to_pascal_case
from sdkgen.utils.case_converter import to_snake_case


PYTHON_KEYWORDS = set(keyword.kwlist)


def sanitize_python_name(name: str, suffix: str = "value") -> str:
    """Convert a string into a valid Python identifier.

    Transforms any string into a valid Python identifier by replacing
    invalid characters, handling numeric prefixes, removing consecutive
    underscores, and handling Python keywords.

    Args:
        name: Original name to sanitize. Can contain any characters.
        suffix: Suffix to append if the sanitized name is a Python keyword
            or if the name is empty after sanitization. Defaults to "value".

    Returns:
        Valid Python identifier that follows naming rules and doesn't
        conflict with Python keywords.

    Example:
        >>> sanitize_python_name("my-variable")
        'my_variable'
        >>> sanitize_python_name("123abc")
        'n123abc'
        >>> sanitize_python_name("class")
        'classvalue'
        >>> sanitize_python_name("!@#")
        'value'
        >>> sanitize_python_name("multiple___underscores")
        'multiple_underscores'
    """
    # Replace invalid characters with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"n{sanitized}"

    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Handle empty string
    if not sanitized:
        sanitized = suffix

    # Handle Python keywords
    if sanitized in PYTHON_KEYWORDS:
        sanitized = f"{sanitized}{suffix}"

    return sanitized


def sanitize_package_name(name: str) -> str:
    """Convert a string into a valid Python package name.

    Converts package names to lowercase, replaces hyphens and spaces with
    underscores, and applies general Python identifier sanitization rules.
    Uses "sdk" as the fallback suffix for empty or keyword names.

    Args:
        name: Original package name. Can contain uppercase letters, hyphens,
            spaces, and other special characters.

    Returns:
        Valid Python package name in lowercase with underscores, following
        PEP 8 package naming conventions.

    Example:
        >>> sanitize_package_name("My-Package")
        'my_package'
        >>> sanitize_package_name("API Client")
        'api_client'
        >>> sanitize_package_name("my-awesome-sdk")
        'my_awesome_sdk'
    """
    # Convert to lowercase
    name = name.lower()

    # Replace hyphens and spaces with underscores
    name = re.sub(r"[-\s]+", "_", name)

    # Use general sanitization
    name = sanitize_python_name(name, suffix="sdk")

    return name


def sanitize_module_name(name: str) -> str:
    """Convert a string into a valid Python module name.

    Module names follow the same conventions as package names in Python.
    This function is an alias for sanitize_package_name.

    Args:
        name: Original module name. Can contain uppercase letters, hyphens,
            spaces, and other special characters.

    Returns:
        Valid Python module name in lowercase with underscores.

    Example:
        >>> sanitize_module_name("MyModule")
        'mymodule'
        >>> sanitize_module_name("api-client")
        'api_client'
    """
    return sanitize_package_name(name)


def sanitize_class_name(name: str) -> str:
    """Convert a string into a valid Python class name (PascalCase).

    First sanitizes the name to be a valid Python identifier, then
    converts it to PascalCase following Python class naming conventions.
    Uses "Class" as the fallback suffix for empty or keyword names.

    Args:
        name: Original class name. Can contain any characters or naming
            convention.

    Returns:
        Valid Python class name in PascalCase (UpperCamelCase) format.

    Example:
        >>> sanitize_class_name("my_class")
        'MyClass'
        >>> sanitize_class_name("api-client")
        'ApiClient'
        >>> sanitize_class_name("HTTPResponse")
        'Httpresponse'
        >>> sanitize_class_name("class")
        'ClassClass'
    """
    # First sanitize as identifier
    sanitized = sanitize_python_name(name, suffix="Class")

    # Convert to PascalCase
    return to_pascal_case(sanitized)


def sanitize_enum_member_name(name: str) -> str:
    """Convert a string into a valid Python enum member name (SCREAMING_SNAKE_CASE).

    First sanitizes the name to be a valid Python identifier, then converts
    it to SCREAMING_SNAKE_CASE following Python enum member naming conventions.
    Uses "VALUE" as the fallback suffix for empty or keyword names.

    Args:
        name: Original enum member name. Can contain any characters or naming
            convention.

    Returns:
        Valid Python enum member name in SCREAMING_SNAKE_CASE (uppercase with
        underscores).

    Example:
        >>> sanitize_enum_member_name("active")
        'ACTIVE'
        >>> sanitize_enum_member_name("in-progress")
        'IN_PROGRESS'
        >>> sanitize_enum_member_name("HTTPError")
        'HTTP_ERROR'
        >>> sanitize_enum_member_name("class")
        'CLASSVALUE'
    """
    # First sanitize as identifier
    sanitized = sanitize_python_name(name, suffix="VALUE")

    # Convert to SCREAMING_SNAKE_CASE
    return to_snake_case(sanitized).upper()

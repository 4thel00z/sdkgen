"""Name sanitization for valid Python identifiers."""

import keyword
import re

from sdkgen.utils.case_converter import to_pascal_case
from sdkgen.utils.case_converter import to_snake_case


PYTHON_KEYWORDS = set(keyword.kwlist)


def sanitize_python_name(name: str, suffix: str = "value") -> str:
    """
    Convert a string into a valid Python identifier.

    Args:
        name: Original name
        suffix: Suffix to add if name is a keyword

    Returns:
        Valid Python identifier
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
    """
    Convert a string into a valid Python package name.

    Args:
        name: Original package name

    Returns:
        Valid Python package name (lowercase, no hyphens)
    """
    # Convert to lowercase
    name = name.lower()

    # Replace hyphens and spaces with underscores
    name = re.sub(r"[-\s]+", "_", name)

    # Use general sanitization
    name = sanitize_python_name(name, suffix="sdk")

    return name


def sanitize_module_name(name: str) -> str:
    """
    Convert a string into a valid Python module name.

    Args:
        name: Original module name

    Returns:
        Valid Python module name
    """
    return sanitize_package_name(name)


def sanitize_class_name(name: str) -> str:
    """
    Convert a string into a valid Python class name (PascalCase).

    Args:
        name: Original class name

    Returns:
        Valid Python class name in PascalCase
    """
    # First sanitize as identifier
    sanitized = sanitize_python_name(name, suffix="Class")

    # Convert to PascalCase
    return to_pascal_case(sanitized)


def sanitize_enum_member_name(name: str) -> str:
    """
    Convert a string into a valid Python enum member name (SCREAMING_SNAKE_CASE).

    Args:
        name: Original enum member name

    Returns:
        Valid Python enum member name in SCREAMING_SNAKE_CASE
    """
    # First sanitize as identifier
    sanitized = sanitize_python_name(name, suffix="VALUE")

    # Convert to SCREAMING_SNAKE_CASE
    return to_snake_case(sanitized).upper()

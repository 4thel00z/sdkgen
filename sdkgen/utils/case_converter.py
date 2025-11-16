"""Case conversion utilities for snake_case ↔ camelCase."""

import re


def to_snake_case(text: str) -> str:
    """
    Convert camelCase or PascalCase to snake_case.

    Args:
        text: String to convert

    Returns:
        snake_case version of the string
    """
    # Insert underscore before uppercase letters
    text = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", text)
    # Handle consecutive uppercase letters (e.g., "HTTPResponse" -> "HTTP_Response")
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    return text.lower()


def to_camel_case(text: str) -> str:
    """
    Convert snake_case to camelCase.

    Args:
        text: String to convert

    Returns:
        camelCase version of the string
    """
    components = text.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_pascal_case(text: str) -> str:
    """
    Convert snake_case to PascalCase.

    Args:
        text: String to convert

    Returns:
        PascalCase version of the string
    """
    return "".join(x.title() for x in text.split("_"))


def detect_naming_convention(text: str) -> str:
    """
    Detect naming convention of a string.

    Args:
        text: String to analyze

    Returns:
        One of: "snake_case", "camelCase", "PascalCase", "SCREAMING_SNAKE_CASE", "unknown"
    """
    if "_" in text:
        if text.isupper():
            return "SCREAMING_SNAKE_CASE"
        return "snake_case"

    if text[0].isupper():
        return "PascalCase"

    if any(c.isupper() for c in text):
        return "camelCase"

    return "unknown"

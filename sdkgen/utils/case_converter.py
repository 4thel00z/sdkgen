"""Case conversion utilities for snake_case ↔ camelCase."""

import re


def to_snake_case(text: str) -> str:
    """Convert camelCase or PascalCase to snake_case.

    Handles multiple naming conventions including camelCase, PascalCase,
    spaces, hyphens, and consecutive uppercase letters (e.g., HTTPResponse).

    Args:
        text: String to convert. Can be in any common naming convention.

    Returns:
        Lowercase snake_case version of the input string with underscores
        separating words.

    Example:
        >>> to_snake_case("camelCase")
        'camel_case'
        >>> to_snake_case("PascalCase")
        'pascal_case'
        >>> to_snake_case("HTTPResponse")
        'http_response'
        >>> to_snake_case("my-kebab-case")
        'my_kebab_case'
    """
    # Replace spaces and hyphens first, then apply regex transformations
    normalized = text.replace(" ", "_").replace("-", "_")
    # Insert underscore before uppercase letters
    with_underscores = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", normalized)
    # Handle consecutive uppercase letters (e.g., "HTTPResponse" -> "HTTP_Response")
    return re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", with_underscores).lower()


def to_camel_case(text: str) -> str:
    """Convert snake_case to camelCase.

    Splits the input string on underscores and capitalizes each word
    except the first one, creating camelCase notation.

    Args:
        text: String to convert, typically in snake_case format.

    Returns:
        camelCase version of the string with the first word lowercase
        and subsequent words capitalized.

    Example:
        >>> to_camel_case("snake_case")
        'snakeCase'
        >>> to_camel_case("multi_word_example")
        'multiWordExample'
        >>> to_camel_case("single")
        'single'
    """
    components = text.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_pascal_case(text: str) -> str:
    """Convert snake_case to PascalCase.

    Splits the input string on underscores and capitalizes all words
    including the first one, creating PascalCase notation (also known
    as UpperCamelCase).

    Args:
        text: String to convert, typically in snake_case format.

    Returns:
        PascalCase version of the string with all words capitalized
        and no underscores.

    Example:
        >>> to_pascal_case("snake_case")
        'SnakeCase'
        >>> to_pascal_case("my_class_name")
        'MyClassName'
        >>> to_pascal_case("single")
        'Single'
    """
    return "".join(x.title() for x in text.split("_"))


def detect_naming_convention(text: str) -> str:
    """Detect the naming convention used in a string.

    Analyzes a string to determine which naming convention it follows
    by checking for underscores, uppercase letters, and letter positions.

    Args:
        text: String to analyze. Should be a single identifier or variable name.

    Returns:
        One of the following naming convention identifiers:
        - "snake_case": lowercase with underscores
        - "camelCase": first word lowercase, subsequent words capitalized
        - "PascalCase": all words capitalized, no separators
        - "SCREAMING_SNAKE_CASE": uppercase with underscores
        - "unknown": doesn't match any recognized pattern

    Example:
        >>> detect_naming_convention("my_variable")
        'snake_case'
        >>> detect_naming_convention("myVariable")
        'camelCase'
        >>> detect_naming_convention("MyClass")
        'PascalCase'
        >>> detect_naming_convention("MY_CONSTANT")
        'SCREAMING_SNAKE_CASE'
        >>> detect_naming_convention("lowercase")
        'unknown'
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

"""Naming utilities for converting between different naming conventions."""

import re
from typing import Optional, Set


def to_snake_case(name: str) -> str:
    """
    Convert string to snake_case.

    Examples:
        >>> to_snake_case("ToolRegistry")
        'tool_registry'
        >>> to_snake_case("Tool Registry API")
        'tool_registry_api'
        >>> to_snake_case("already_snake_case")
        'already_snake_case'
    """
    # Remove special characters except spaces and hyphens
    name = re.sub(r"[^\w\s-]", "", name)

    # Convert to lowercase and replace spaces/hyphens with underscores
    name = re.sub(r"[-\s]+", "_", name.lower())

    # Handle camelCase and PascalCase
    # Insert underscore before uppercase letters
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)

    # Clean up multiple underscores
    name = re.sub(r"_+", "_", name)

    # Remove leading/trailing underscores
    return name.strip("_").lower()


def to_pascal_case(name: str) -> str:
    """
    Convert string to PascalCase.

    Examples:
        >>> to_pascal_case("tool_registry")
        'ToolRegistry'
        >>> to_pascal_case("user id")
        'UserId'
        >>> to_pascal_case("AlreadyPascal")
        'AlreadyPascal'
    """
    # First, handle camelCase/PascalCase by inserting delimiters
    # e.g., "ArtifactOut" -> "Artifact_Out"
    name_with_delimiters = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name_with_delimiters = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name_with_delimiters)

    # Split on underscores, spaces, and hyphens
    words = re.split(r"[_\s-]+", name_with_delimiters)

    # Capitalize first letter of each word, preserve rest
    return "".join(word[0].upper() + word[1:] if word else "" for word in words if word)


def to_camel_case(name: str) -> str:
    """
    Convert string to camelCase.

    Examples:
        >>> to_camel_case("tool_registry")
        'toolRegistry'
        >>> to_camel_case("user id")
        'userId'
    """
    pascal = to_pascal_case(name)
    if not pascal:
        return ""
    return pascal[0].lower() + pascal[1:]


def sanitize_package_name(name: str) -> str:
    """
    Sanitize a string to be a valid Python package name.

    Examples:
        >>> sanitize_package_name("Tool Registry API 2.0")
        'tool_registry_api_2_0'
        >>> sanitize_package_name("@special/name")
        'special_name'
    """
    # Remove any non-alphanumeric characters except spaces and hyphens
    name = re.sub(r"[^\w\s-]", "", name)

    # Convert to snake_case
    name = to_snake_case(name)

    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"api_{name}"

    return name or "api_client"


def sanitize_class_name(name: str) -> str:
    """
    Sanitize a string to be a valid Python class name.

    Examples:
        >>> sanitize_class_name("user-model")
        'UserModel'
        >>> sanitize_class_name("2fa_config")
        'TwoFaConfig'
    """
    # Remove special characters
    name = re.sub(r"[^\w\s-]", "", name)

    # Convert to PascalCase
    name = to_pascal_case(name)

    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        # Convert leading digits to words
        digit_words = {
            "0": "Zero",
            "1": "One",
            "2": "Two",
            "3": "Three",
            "4": "Four",
            "5": "Five",
            "6": "Six",
            "7": "Seven",
            "8": "Eight",
            "9": "Nine",
        }
        first_char = name[0]
        name = digit_words.get(first_char, "Number") + name[1:]

    return name or "Model"


def sanitize_method_name(name: str) -> str:
    """
    Sanitize a string to be a valid Python method name.

    Examples:
        >>> sanitize_method_name("getUsers")
        'get_users'
        >>> sanitize_method_name("POST /users")
        'post_users'
    """
    # Remove special characters except spaces and underscores
    name = re.sub(r"[^\w\s]", "", name)

    # Convert to snake_case
    name = to_snake_case(name)

    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"operation_{name}"

    return name or "operation"


def sanitize_field_name(name: str, reserved_keywords: Optional[Set[str]] = None) -> str:
    """
    Sanitize a string to be a valid Python field name.

    Args:
        name: The field name to sanitize
        reserved_keywords: Set of Python keywords to avoid (defaults to common keywords)

    Examples:
        >>> sanitize_field_name("user-id")
        'user_id'
        >>> sanitize_field_name("class")
        'class_'
        >>> sanitize_field_name("2fa_enabled")
        'two_fa_enabled'
    """
    if reserved_keywords is None:
        reserved_keywords = {
            "class",
            "def",
            "return",
            "if",
            "else",
            "elif",
            "for",
            "while",
            "break",
            "continue",
            "import",
            "from",
            "as",
            "try",
            "except",
            "finally",
            "raise",
            "with",
            "pass",
            "lambda",
            "yield",
            "global",
            "nonlocal",
            "assert",
            "del",
            "and",
            "or",
            "not",
            "is",
            "in",
            "type",
            "id",
        }

    # Convert to snake_case
    name = to_snake_case(name)

    # Handle leading digits
    if name and name[0].isdigit():
        digit_words = {
            "0": "zero",
            "1": "one",
            "2": "two",
            "3": "three",
            "4": "four",
            "5": "five",
            "6": "six",
            "7": "seven",
            "8": "eight",
            "9": "nine",
        }
        first_char = name[0]
        name = digit_words.get(first_char, "number") + "_" + name[1:]

    # Avoid reserved keywords
    if name in reserved_keywords:
        name = f"{name}_"

    return name or "field"

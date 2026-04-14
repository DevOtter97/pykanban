"""Shared field validators."""

FORBIDDEN_STRINGS = {"undefined", "null", "none", ""}


def validate_not_undefined(v: str, field_name: str) -> str:
    if v.strip().lower() in FORBIDDEN_STRINGS:
        raise ValueError(f"{field_name} cannot be empty or undefined")
    return v

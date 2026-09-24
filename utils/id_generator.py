"""Centralized unique ID generation for synthetic hospital data."""

import random
import string

# All IDs generated during one main.py run are tracked here.
_USED_IDS = set()

# 4-character suffix => 36^4 = 1,679,616 possibilities per prefix.
_ALPHANUMERIC = string.ascii_uppercase + string.digits

PREFIXES = {
    "hospital": "HO",
    "department": "DE",
    "doctor": "DO",
    "patient": "PA",
    "visit": "VI",
    "admission": "AD",
    "billing": "BI",
    "diagnostic": "DI",
    "surgery": "SU",
}


def generate_id(entity_type: str) -> str:
    """Return a unique six-character ID for an entity type."""
    if entity_type not in PREFIXES:
        raise ValueError(
            f"Unknown entity type: {entity_type}. "
            f"Use one of: {', '.join(PREFIXES)}"
        )

    prefix = PREFIXES[entity_type]

    while True:
        suffix = "".join(
            random.choices(_ALPHANUMERIC, k=4)
        )
        value = f"{prefix}{suffix}"

        if value not in _USED_IDS:
            _USED_IDS.add(value)
            return value


def reset_ids() -> None:
    """Clear the ID registry before a completely new generation run."""
    _USED_IDS.clear()


def validate_id(value: str, entity_type: str) -> bool:
    """Validate an ID's prefix, length, and allowed characters."""
    if entity_type not in PREFIXES:
        return False

    return (
        isinstance(value, str)
        and len(value) == 6
        and value.startswith(PREFIXES[entity_type])
        and all(ch in _ALPHANUMERIC for ch in value[2:])
    )

"""tmxkit.tu

Utilities for operations inside a `<tu>` (Translation Unit).

Main modules:
- ``props`` — extraction, retrieval and replacement utilities for ``<prop>``
        (``extract_props``, ``get_prop_value``, ``replace_prop_value``)
- ``segment`` — retrieval and replacement helpers for ``<seg>`` / ``<tuv>``
        (``get_segment``, ``get_seg_inner_xml``, etc.)
- ``normalize`` — normalization and minor transformation utilities (provides
        normalization rules)

These are small helpers that accept a TU as input and perform element
retrieval and updates via DOM operations.
"""

from . import normalize
from .props import extract_props, get_prop_value, replace_prop_value
from .segment import (
        get_segment,
        replace_text,
)

__all__ = [
        'extract_props', 'get_prop_value', 'replace_prop_value',
        'get_segment', 'replace_text',
        'normalize',
]

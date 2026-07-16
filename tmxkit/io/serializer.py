"""Serialize a tu"""
from __future__ import annotations

import lxml.etree as etree


def serialize_tu(tu_elem: etree.Element) -> bytes:
    """Serialize ``tu_elem`` to bytes without adding extra newlines."""
    return etree.tostring(
        tu_elem,
        encoding='utf-8',
        xml_declaration=False,
        pretty_print=False,
    )

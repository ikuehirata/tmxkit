"""Normalization and light processing.

This module provides utilities for normalizing whitespace and performing
minor text cleanups used for TMX segment content.
"""
import re


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace and line breaks.

    Parameters
    ----------
    text : str
        The string to normalize.

    Returns
    -------
    str
        The normalized string.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\u00a0', ' ')   # NBSP
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

"""Merge and split"""
from __future__ import annotations

import lxml.etree as etree

from ..errors import InvalidTUError


def merge_streams(*streams):
    """Merge multiple TU streams into a single TU stream.

    Yields TUs from each provided stream in sequence.
    """
    for stream in streams:
        for tu in stream:
            if not isinstance(tu, etree.Element):
                raise InvalidTUError('merge_streams expects tu elements')
            yield tu

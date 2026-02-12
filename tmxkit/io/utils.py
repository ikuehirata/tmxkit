"""Utility functions for TMX file I/O.

These helpers provide lightweight parsing utilities used to extract the
``<header>`` or the first ``<tu>`` element from a TMX file without loading
the entire document into memory.
"""
from pathlib import Path

import lxml.etree as etree


def get_header_xml(path: Path) -> etree.Element | None:
    """Read and return only the ``<header>`` element from a TMX file.

    This uses incremental parsing to stop as soon as a header element is
    encountered.
    """
    for event, elem in etree.iterparse(
        str(path),
        events=('end',),
        tag='header',
        recover=True,
        huge_tree=True,
    ):
        # header を見つけた瞬間に返す
        return elem

    return None


def get_first_tu_xml(path: Path) -> etree.Element | None:
    """Read and return the first ``<tu>`` element from a TMX file.

    Uses incremental parsing and returns as soon as the first TU is found.
    """
    for event, elem in etree.iterparse(
        str(path),
        events=('end',),
        tag='tu',
        recover=True,
        huge_tree=True,
    ):
        # 最初の tu を見つけた瞬間に返す
        return elem

    return None

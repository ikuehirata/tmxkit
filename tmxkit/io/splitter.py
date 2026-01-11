"""Utilities to split a single TMX into multiple outputs.

Header handling is not considered by these helpers.
"""

from pathlib import Path
from typing import Callable, Iterable

import lxml.etree as etree

from .serializer import serialize_tu
from .writer import _write_footter, _write_header


def split_stream(
        tu_stream: Iterable[etree.Element],
        classify: Callable[[etree.Element], str],
        out_path_for: Callable[[str], Path]) -> int:
    """Split a TU stream and write each TU to an output according to ``classify``.

    Header handling is not performed by this function.

    Parameters
    ----------
    tu_stream : Iterable[etree.Element]
        The TU stream to split.
    classify : Callable[[etree.Element], str]
        Function that classifies a TU and returns a string key.
    out_path_for : Callable[[str], Path]
        Function that returns an output path for a given classification key.

    Returns
    -------
    int
        Total number of TUs written.
    """
    writers = {}
    counter = 0

    for tu in tu_stream:
        key = classify(tu)
        if key is None:
            continue
        path = out_path_for(key)

        writer = _get_writer(path, writers)
        writer.write(serialize_tu(tu))
        counter += 1

    _close_writers(writers)
    return counter


def _get_writer(path: Path, writers_dict: dict):
    """Get or create a file writer for the given ``path``.

    This helper is designed for continuous write use-cases.

    Parameters
    ----------
    path : pathlib.Path
        The output path.
    writers_dict : dict
        Dictionary of current writers used during processing.
    """
    if path not in writers_dict:
        path.parent.mkdir(parents=True, exist_ok=True)
        writers_dict[path] = open(path, 'wb')
        # <body> タグまでを書き出す
        _write_header(None, writers_dict[path])
    return writers_dict[path]


def _close_writers(writers_dict: dict) -> None:
    """Close all file objects contained in ``writers_dict``."""
    for f_writer in writers_dict.values():
        # </body> タグから後を書き出す
        _write_footter(f_writer)
        f_writer.close()
    writers_dict.clear()

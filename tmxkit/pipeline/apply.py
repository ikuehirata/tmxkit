"""Just streams the tu_processor"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import TypeAlias, Union

import lxml.etree as etree

TU: TypeAlias = etree.Element
Processor = Callable[[TU], Union[TU, None]]
ErrorHandler = Callable[[TU, Exception], None]


def apply(
    tu_stream: Iterable[TU],
    processor: Processor,
    on_error: ErrorHandler | None = None,
) -> Iterator[TU]:
    """Apply ``processor`` to each TU from ``tu_stream``.

    Processes all TUs while also recording any that fail processing.

    Parameters
    ----------
    tu_stream : Iterable[TU]
        Input TU stream.
    processor : Processor
        Processing applied to each TU. Returns a TU or None.
    on_error : ErrorHandler | None, optional
        Callback invoked when an exception occurs. Called with the
        original TU and the error. If not given, exceptions are silently
        ignored.

    Yields
    ------
    TU
        The TU returned by processor (None is discarded).

    Notes
    -----
    - A TU for which processor returns None is discarded.
    - Processing continues even if an exception occurs.
    """
    for tu in tu_stream:
        try:
            new_tu = processor(tu)
        except Exception as e:
            if on_error:
                on_error(tu, e)
            continue
        if new_tu is None:
            continue
        yield new_tu

"""Apply a TU processor to a stream of TUs."""
from collections.abc import Callable, Iterable, Iterator
from typing import TypeAlias

import lxml.etree as etree

TU: TypeAlias = etree.Element
Processor = Callable[[TU], TU | None]


def apply(
    tu_stream: Iterable[TU],
    processor: Processor,
) -> Iterator[TU]:
    """Apply ``processor`` to each TU from ``tu_stream``.

    - ``processor`` receives a TU and returns a TU or ``None``.
    - TUs for which ``processor`` returns ``None`` are discarded.
    """
    for tu in tu_stream:
        try:
            new_tu = processor(tu)
        except Exception as e:
            from ..errors import StreamError
            raise StreamError('processor raised an exception') from e
        if new_tu is None:
            continue
        yield new_tu

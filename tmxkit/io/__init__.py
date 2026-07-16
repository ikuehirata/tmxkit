"""tmxkit.io

Subpackage providing streaming I/O utilities for TMX.

Main modules:
- `reader` — `stream_tu`, which reads `<tu>` elements sequentially from a large TMX
- `writer` — `write_tu_stream`, which writes a TMX sequentially from a TU stream
- `merger` — `merge_streams`, which merges multiple TU streams

This package re-exports common exceptions raised during I/O operations.
"""
from __future__ import annotations

from ..errors import InvalidTUError, StreamError, TmxkitError, TmxParseError
from .merger import merge_streams
from .reader import parse_header, stream_tu, stream_tu_fragment
from .serializer import serialize_tu
from .writer import write_tu_stream

__all__ = [
    'stream_tu', 'stream_tu_fragment', 'parse_header',
    'write_tu_stream',
    'serialize_tu',
    'merge_streams',
    'TmxkitError', 'TmxParseError', 'InvalidTUError', 'StreamError',
    'write_tu_stream',
]

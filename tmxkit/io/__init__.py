"""tmxkit.io

Subpackage providing streaming I/O utilities for TMX.

Main modules:
- ``reader`` — ``stream_tu`` to sequentially read ``<tu>`` elements from large
    TMX files
- ``writer`` — ``write_from_roots`` / ``write_from_root`` to write TMX from a
    stream of TUs
- ``merger`` — ``merge_streams`` to merge multiple TU streams

This package re-exports common exceptions raised during I/O operations.
"""

from ..errors import InvalidTUError, StreamError, TmxkitError, TmxParseError
from .merger import merge_streams
from .reader import read_header_only, stream_tu
from .serializer import serialize_tu
from .writer import (
    write_tu_stream,
)

__all__ = [
    'stream_tu', 'read_header_only',
    'write_tu_stream',
	'serialize_tu',
    'merge_streams',
    'TmxkitError', 'TmxParseError', 'InvalidTUError', 'StreamError',
]

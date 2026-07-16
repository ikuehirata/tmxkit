"""tmxkit.pipeline

Provides a thin helper layer to apply processing functions (processors) to a
TU stream.

Main feature:
- ``apply`` — an iterator that takes TUs sequentially and yields processed
  TUs from ``processor(tu)``.

The pipeline is intentionally thin; the processing responsibility remains with
the caller-provided ``processor``.
"""
from __future__ import annotations

from .apply import apply

__all__ = ['apply']

"""tmxkit.ops — Subpackage providing a high-level API for TMX file operations.

Gathers functions that let you perform operations like merge and split by
simply passing file paths, without worrying about assembling low-level
streams.
"""
from __future__ import annotations

from .export import to_csv
from .merge import merge
from .split import split

__all__ = ['merge', 'split', 'to_csv']

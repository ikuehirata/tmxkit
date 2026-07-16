"""tmxkit.ops.split — Provides a high-level function to route a TMX file using a classifier function."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Union

import lxml.etree as etree

# io を先に import することで core.models の循環 import を回避する
from tmxkit.io import stream_tu
from tmxkit.io.splitter_sink import consume_and_split
from tmxkit.pipeline import apply
from tmxkit.core.models import TMXHeader

Processor = Callable[[etree.Element], Union[etree.Element, None]]


def split(
    input: str | Path,
    key_extractor: Callable[[etree.Element], str | None],
    output_dir: str | Path,
    *,
    header: str | Path | None = None,
    processors: list[Processor] | None = None,
    error_path: str | Path | None = None,
) -> dict[str, int]:
    """Route a TMX file using a classifier function and write it out to output_dir.

    Parameters
    ----------
    input : str | Path
        Input TMX file path.
    key_extractor : Callable[[etree.Element], str | None]
        Function that receives a TU element and returns a classification
        key that becomes the output file name (without extension).
        TUs for which it returns ``None`` are skipped.
    output_dir : str | Path
        Output directory. Created automatically if it doesn't exist.
    header : str | Path | None
        TMX file path to use as the header.
        If ``None``, uses the header of ``input``.
    processors : list[Processor] | None
        List of processors applied in order to the TU stream.
        If None or an empty list, TUs pass through unchanged.
    error_path : str | Path | None
        File path for saving TUs that failed to write on error.
        If ``None``, auto-generated in the same directory as each output file.

    Returns
    -------
    dict[str, int]
        Dictionary of ``{output file path string: number of TUs written}``.

    Raises
    ------
    FileNotFoundError
        If the file given for ``input`` or ``header`` doesn't exist.
    """
    input_path = Path(input)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f'Input file not found: {input_path}')

    header_path = Path(header) if header is not None else None
    if header_path is not None and not header_path.exists():
        raise FileNotFoundError(f'Header file not found: {header_path}')

    if header_path is not None:
        header_obj = TMXHeader.from_tmx_file(header_path)
    else:
        header_obj = TMXHeader.from_tmx_file(input_path)

    tu_stream = stream_tu(input_path)
    for proc in (processors or []):
        tu_stream = apply(tu_stream, proc)

    return consume_and_split(
        input_stream=tu_stream,
        key_extractor=key_extractor,
        header_obj=header_obj,
        base_dir=output_path,
        error_path=Path(error_path) if error_path is not None else None,
    )

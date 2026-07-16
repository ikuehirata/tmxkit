"""tmxkit.ops.merge — Provides a high-level function to merge multiple TMX files into one."""
from __future__ import annotations

import logging
import shutil
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Union

import lxml.etree as etree

from tmxkit.core.models import TMXHeader

# io を先に import することで core.models の循環 import を回避する
from tmxkit.io import merge_streams, stream_tu, write_tu_stream
from tmxkit.pipeline import apply

logger = logging.getLogger(__name__)

Processor = Callable[[etree.Element], Union[etree.Element, None]]


def merge(
    inputs: Sequence[str | Path],
    output: str | Path,
    *,
    header: str | Path | None = None,
    processors: list[Processor] | None = None,
    error_path: str | Path | None = None,
    backup: bool = True,
    strict: bool = False,
) -> int:
    """Merge multiple TMX files into one and write the result to output.

    Parameters
    ----------
    inputs : Sequence[str | Path]
        List of input TMX file paths (one or more).
    output : str | Path
        Output TMX file path. **If a file already exists there, it is
        appended to** (not overwritten). Note that running merge multiple
        times with the same inputs will duplicate TUs. This is the intended
        usage for incrementally stacking merges; if you want a fresh
        output every time, delete the output beforehand on the caller side.
    header : str | Path | None
        TMX file path to use as the header.
        If None, uses the header of inputs[0].
    processors : list[Processor] | None
        List of processors applied in order to the TU stream.
        If None or an empty list, TUs pass through unchanged.
    error_path : str | Path | None
        File path for saving TUs that failed to write on error.
        If ``None``, ``{output.stem}_error.tmx`` is auto-generated.
    backup : bool
        If True, when output already exists, creates a backup at
        ``{output.stem}.bak``. Deleted after a successful merge. Kept if
        the merge fails or the TU count doesn't match.
    strict : bool
        If True, raises ``ValueError`` when **the total TU count of the
        output file** doesn't match "existing TU count before the merge
        started + this run's input TU count" (since appending to output is
        assumed, this validates against the whole file, not just this
        run's portion). Leave this False when filtering with processors.

    Returns
    -------
    int
        Number of TUs written out by this call (not including any TUs
        that already existed in output).

    Raises
    ------
    FileNotFoundError
        If a file given for inputs or header doesn't exist.
    ValueError
        If inputs is an empty list, or if strict=True and the TU count
        doesn't match.
    """
    if not inputs:
        raise ValueError('inputs must specify one or more file paths')

    input_paths = [Path(p) for p in inputs]
    output_path = Path(output)
    bak_path = output_path.with_suffix('.bak')

    for p in input_paths:
        if not p.exists():
            raise FileNotFoundError(f'Input file not found: {p}')

    header_path = Path(header) if header is not None else None
    if header_path is not None and not header_path.exists():
        raise FileNotFoundError(f'Header file not found: {header_path}')

    # バックアップ作成
    if backup and output_path.exists():
        shutil.copy2(output_path, bak_path)
        logger.debug('merge: backup created at %s', bak_path)

    try:
        if header_path is not None:
            header_obj = TMXHeader.from_tmx_file(header_path)
        else:
            header_obj = TMXHeader.from_tmx_file(input_paths[0])

        # output は追記されるため、開始前の既存 TU 数を検証用に控えておく
        existing_count = 0
        if strict and output_path.exists():
            existing_count = sum(1 for _ in stream_tu(output_path))

        streams = (stream_tu(p) for p in input_paths)
        merged = merge_streams(*streams)

        input_count = 0

        def _count_input(tu: etree.Element) -> etree.Element:
            nonlocal input_count
            input_count += 1
            return tu

        tu_stream = (_count_input(tu) for tu in merged)
        for proc in (processors or []):
            tu_stream = apply(tu_stream, proc)

        output_count = write_tu_stream(
            tu_stream=tu_stream,
            header_obj=header_obj,
            out_path=output_path,
            error_path=Path(error_path) if error_path is not None else None,
        )

        logger.info(
            'merge: %d input file(s), input TUs: %d, appended TUs: %d',
            len(input_paths), input_count, output_count,
        )

        if strict:
            # output は追記されるため、検証は出力ファイル全体の TU 数で行う
            final_total = sum(1 for _ in stream_tu(output_path))
            expected_total = existing_count + input_count
            if final_total != expected_total:
                logger.warning(
                    'merge TU count mismatch: expected=%d (existing=%d + input=%d), '
                    'actual=%d (diff=%d)',
                    expected_total, existing_count, input_count,
                    final_total, expected_total - final_total,
                )
                if backup:
                    logger.warning('merge: backup preserved for recovery at %s', bak_path)
                raise ValueError(
                    f'TU count mismatch: expected={expected_total} '
                    f'(existing={existing_count} + input={input_count}), '
                    f'actual output={final_total} (diff={expected_total - final_total})'
                )
            else:
                if backup:
                    bak_path.unlink(missing_ok=True)
                    logger.debug('merge: backup removed (TU count verified)')
        else:
            if input_count != output_count:
                logger.warning(
                    'merge TU count mismatch (non-strict): input=%d, appended=%d (diff=%d)',
                    input_count, output_count, input_count - output_count,
                )
                if backup:
                    logger.warning('merge: backup preserved for recovery at %s', bak_path)
            else:
                if backup:
                    bak_path.unlink(missing_ok=True)
                    logger.debug('merge: backup removed (TU count verified)')

    except Exception:
        if backup:
            logger.warning('merge: failed; backup preserved for recovery at %s', bak_path)
        raise

    return output_count

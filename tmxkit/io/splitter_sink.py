"""TMX split and sink functionality."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterable

import lxml.etree as etree

from ..core.models import TMXHeader
from .writer import TMXWriter, WriterRouter, default_output_resolver, default_writer_factory

logger = logging.getLogger(__name__)


def consume_and_split(
    input_stream: Iterable[etree.Element],
    key_extractor: Callable[[etree.Element], str | None],
    output_resolver: Callable[[str], Path] | None = None,
    writer_factory: Callable[[Path], TMXWriter] | None = None,
    header_path: Path | None = None,
    header_obj: TMXHeader | None = None,
    buffer_size: int = 200,
    max_writers: int = 100,
    base_dir: Path = Path('.'),
    error_path: Path | None = None,
) -> dict[str, int]:
    """Consume a TU stream sequentially and split it into TMX files by category.

    Parameters
    ----------
    input_stream : Iterable[etree.Element]
        An iterator of TU elements to consume.
    key_extractor : Callable[[etree.Element], str | None]
        Function that extracts a classification key from a TU element. If
        the function returns ``None`` the TU is ignored.
    output_resolver : Callable[[str], Path] | None
        Function to map a classification key to an output file Path. If
        ``None``, a default resolver is used.
    writer_factory : Callable[[Path], TMXWriter] | None
        Factory to create a ``TMXWriter`` for a given output Path. If
        ``None``, a default factory will be created.
    header_path : Path | None
        Path to a TMX file used to obtain header information for outputs.
        If ``None``, a default header is used.
    header_obj : TMXHeader | None
        Optional ``TMXHeader`` instance to use directly for output. If
        provided, this takes precedence over ``header_path``.
    buffer_size : int
        Buffer size for individual writers (number of TUs before flush).
    max_writers : int
        Maximum number of concurrently open writers.
    base_dir : Path
        Base directory for output file paths. Default is the current directory.
    error_path : Path | None
        File path for saving TUs that failed to write on error.
        If ``None``, each writer uses its own auto-generated path.

    Returns
    -------
    dict[str, int]
        Mapping from output file path strings to the number of TUs written.
    """
    base_dir = Path(base_dir)
    # 出力先を作成しておく
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)

    # output_resolver が指定されなければデフォルトを用意
    if output_resolver is None:
        def _bound_output_resolver(k: str) -> Path:
            return default_output_resolver(key=k, ext='.tmx')
        output_resolver = _bound_output_resolver

    # デフォルト writer_factory を用意
    if writer_factory is None:
        writer_factory = default_writer_factory(
            base_dir=base_dir,
            header_path=header_path,
            header_obj=header_obj,
            buffer_size=buffer_size,
            error_path=error_path,
        )

    router = WriterRouter(writer_factory=writer_factory, max_writers=max_writers)
    stats: dict[str, int] = {}

    try:
        for tu in input_stream:
            try:
                key = key_extractor(tu)
            except Exception:
                logger.exception('key_extractor failed')
                continue

            if key is None:
                continue

            out_path = output_resolver(key)
            writer = router.get_or_create(out_path)
            writer.append(tu)
            stats_key = str(out_path)
            stats[stats_key] = stats.get(stats_key, 0) + 1

    finally:
        router.flush_all()
        router.close_all()

    return stats

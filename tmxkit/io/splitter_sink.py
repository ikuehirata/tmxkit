"""TMX split and sink functionality."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterable

import lxml.etree as etree

from .writer import TMXWriter, WriterRouter, default_output_resolver, default_writer_factory


def consume_and_split(
    input_stream: Iterable[etree.Element],
    key_extractor: Callable[[etree.Element], str | None],
    output_resolver: Callable[[str], Path] | None = None,
    writer_factory: Callable[[Path], TMXWriter] | None = None,
    header_path: Path | None = None,
    buffer_size: int = 200,
    max_writers: int = 100,
    base_dir: Path | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, int]:
    """Consume a TU stream sequentially and split it into TMX files by category.

    Returns
    -------
    dict[str, int]
        Mapping from output file path strings to the number of TUs written.
    """
    logger = logger or logging.getLogger(__name__)
    base_dir = Path(base_dir) if base_dir is not None else Path('.')

    # output_resolver が指定されなければデフォルトを用意
    if output_resolver is None:
        def _bound_output_resolver(k: str) -> Path:
            return default_output_resolver(key=k, base_dir=base_dir, ext='.tmx')
        output_resolver = _bound_output_resolver

    # デフォルト writer_factory を用意
    if writer_factory is None:
        writer_factory = default_writer_factory(
            base_dir=base_dir,
            header_path=header_path,
            buffer_size=buffer_size
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

"""Read `input.tmx` and split the TMX by the value of `<prop type="x-document">`.

Usage::

    python run.py

The script reads `input.tmx` in the same directory and writes split TMX
files into the `split/` subdirectory.
"""

from __future__ import annotations

import re
from pathlib import Path

from tmxkit.io import parse_header, stream_tu
from tmxkit.io.splitter_sink import consume_and_split


def _classify_by_x_document(tu) -> str | None:
    """Return the value of ``<prop type="x-document">`` as a classification key.

    The returned key is the prop value with its file extension removed. If
    the property is not found, ``None`` is returned and the TU is excluded
    from splitting.
    """
    prop = tu.find('prop[@type="x-document"]')
    if prop is None:
        return None
    filename = (prop.text or '').strip()
    return re.sub(r'\.[^.]+$', '', filename)


def main() -> None:
    """Entry point.

    Reads ``input.tmx`` in the same directory and splits it by the value of
    ``<prop type="x-document">``, writing results under the ``split/``
    subdirectory.
    """
    base = Path(__file__).parent
    input_path = base / 'input.tmx'
    out_dir = base / 'split'

    tmx_header = parse_header(input_path)
    tu_stream = stream_tu(input_path)

    written = consume_and_split(
        input_stream=tu_stream,
        key_extractor=_classify_by_x_document,
        header_obj=tmx_header,
        base_dir=out_dir,
    )
    print(written)

    total = sum(written.values())
    print(f'saved TUs: {total}')


if __name__ == '__main__':
    main()


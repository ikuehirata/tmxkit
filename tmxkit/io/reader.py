"""Reading utilities (streaming)."""

from pathlib import Path
from typing import Iterator

import lxml.etree as etree

from ..core.models import TMXHeader
from ..errors import StreamError, TmxParseError


def parse_header(path: Path) -> TMXHeader:
    """Read the ``<header>`` element from a TMX file and return a ``TMXHeader``.

    This is a thin helper around ``TMXHeader.from_tmx_file`` for convenience.
    """
    header = TMXHeader.from_tmx_file(path)
    return header


def stream_tu(input_file: str | Path) -> Iterator[etree.Element]:
    """Generator that yields TU elements from a TMX file or a TU-only file.

    Notes
    -----
    - Uses ``iterparse`` to process large TMX files without loading the whole
        document into memory.
    - If the input is a TU-only file (not a well-formed XML document), the
        function attempts a fallback parse by wrapping the content.
    """
    try:
        # 正常な TMX ファイルとして逐次パースする
        for event, elem in etree.iterparse(
                str(input_file),
                events=('end',),
                tag='tu',
                recover=True,
                huge_tree=True,
        ):
            yield elem

            # 安全な解放
            elem.clear()

            while elem.getprevious() is not None:
                del elem.getparent()[0]

    except etree.XMLSyntaxError:
        # TU のみのファイルの場合（有効な XML になっていない）
        # input_file が Path の場合のみ fallback を試みる
        if isinstance(input_file, Path):
            try:
                root = etree.fromstring(input_file.read_bytes())
                for tu in root.findall('tu'):
                    yield tu
            except Exception as e:
                raise TmxParseError(f'Failed to parse TU-only file: {input_file}') from e
        else:
            raise TmxParseError(f'XML syntax error while parsing: {input_file}')
    except Exception as e:
        raise StreamError(f'Unexpected error while streaming TU from {input_file}') from e

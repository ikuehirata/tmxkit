"""Writing utilities (streaming)."""

import warnings
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import BinaryIO, Callable, Iterable

import lxml.etree as etree

from ..errors import StreamError
from .reader import read_header_only


def is_tmx_header(elem: etree.Element) -> bool:
    """Return True if ``elem`` is a TMX ``<header>`` element."""
    q = etree.QName(elem)
    if q.localname != 'header':
        return False
    parent = elem.getparent()
    return parent is not None and etree.QName(parent).localname == 'tmx'


def make_default_header() -> etree.Element:
    """Create a default ``<header>`` element containing tmxkit version info."""
    try:
        v = version('tmxkit')
    except PackageNotFoundError:
        v = 'unknown'

    header = etree.Element(
        'header',
        creationtool='tmxkit',
        creationtoolversion=v,
    )
    return header


def _write_header(header: etree.Element | None, out_f: BinaryIO) -> None:
    """Write the TMX header and opening body tags to the output stream."""
    # XML 宣言は最初に書く
    out_f.write(
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<!DOCTYPE tmx SYSTEM "tmx14.dtd">\n'
        b'<tmx version="1.4">\n'
    )

    # header が tmx の header かどうかを判定
    if header is not None and not is_tmx_header(header):
        warnings.warn(
            '⚠️ The provided header is not a TMX header.'
            ' Recommended code:\n'
            'import tmxkit\n'
            'header = tmxkit.io.reader.read_header_only(input_path)\n',
            category=DeprecationWarning,
            stacklevel=2,
        )
        # header が tmx でなければ、tmx の子要素として header を探す
        root = header
        header = root.find('header')

    # ヘッダが存在しない場合はデフォルトを作成
    if header is None:
        header = make_default_header()
        # TODO 確認事項：srclang='en' は必要。そのままmemoQにインポートできる？

    # <header> を書き出す
    out_f.write(etree.tostring(header, encoding='utf-8'))

    # body の開始タグを書き出す
    out_f.write(b'<body>\n')


def _write_footter(out_f: BinaryIO) -> None:
    """Write the TMX footer (closing body and tmx tags) to the output.

    Note: function name intentionally contains a typo to match original
    implementation (``_write_footter``).
    """
    out_f.write(b'</body>\n')
    out_f.write(b'</tmx>\n')


def write_from_root(
        input_path: str | Path, final_path: str | Path, tu_processor: Callable) -> None:
    """Write a TMX file from an XML root, applying ``tu_processor`` to each TU.

    Parameters
    ----------
    input_path : str | pathlib.Path
        Source file path.
    final_path : str | pathlib.Path
        Destination file path.
    tu_processor : callable
        A function that accepts a TU element and returns a processed TU.

    Notes
    -----
    - Output is written in binary mode. If no TUs are written, the
      implementation may fallback to writing an empty TMX.
    """
    warnings.warn(
        '⚠️ write_from_root is deprecated. Please update your code accordingly.',
        DeprecationWarning)

    from ..pipeline.apply import apply
    from .reader import stream_tu
    # applyを使って tu_processor を TU ストリームに適用する
    tu_stream = stream_tu(input_path)
    tu_stream = apply(tu_stream, tu_processor)

    try:
        _ = write_tu_stream(
            tu_stream=tu_stream,
            header_root=read_header_only(Path(input_path)),
            final_path=Path(final_path)
        )
    except Exception as e:
        raise StreamError(f'Failed to write TMX from root: {input_path} -> {final_path}') from e


def write_from_roots(
        input_paths: Iterable[str | Path],
        final_path: str | Path,
        tu_processor: Callable) -> None:
    """Write multiple XML roots into a single TMX file.

    Parameters
    ----------
    input_paths : Iterable[str | Path]
        Iterable of source file paths.
    final_path : str | Path
        Destination file path.
    tu_processor : Callable
        Function that processes each TU and returns a TU or ``None``.

    """
    warnings.warn(
        '⚠️ write_from_roots is deprecated. Please update your code accordingly.',
        DeprecationWarning)

    import itertools

    from ..pipeline.apply import apply
    from .merger import merge_streams
    from .reader import stream_tu

    # イテレータを使って先頭ファイルを取り出し、全体は逐次処理する（メモリ節約）
    it = iter(input_paths)
    first = next(it, None)
    if first is None:
        return

    # input_paths からストリームを統合
    # 各入力を逐次 stream_tu に変換して merge_streams に渡す
    merged_tu_stream = merge_streams(*(stream_tu(p) for p in itertools.chain([first], it)))
    merged_tu_stream = apply(merged_tu_stream, tu_processor)

    # ヘッダは最初のファイルから取得
    header_root = read_header_only(Path(first))
    try:
        _ = write_tu_stream(
            tu_stream=merged_tu_stream,
            header_root=header_root,
            final_path=Path(final_path)
        )
    except Exception as e:
        raise StreamError(
            f'Failed to write TMX from roots: {input_paths} -> {final_path}') from e


def write_tu_stream(
    tu_stream: Iterable[etree.Element],
    header_root: etree.Element,
    final_path: Path,
) -> int:
    """Write a TMX file from a stream of TUs.

    Parameters
    ----------
    tu_stream : Iterable[etree.Element]
        An iterable of TU elements.
    header_root : etree.Element
        Root element containing header information for the output TMX.
    final_path : pathlib.Path
        Destination file path.

    Returns
    -------
    int
        The number of TUs written.

    Notes
    -----
    - Output is written in binary mode. If no TUs are written, the
      implementation may create an empty TMX file.
    """
    tu_count = 0
    final_path.parent.mkdir(parents=True, exist_ok=True)

    with open(final_path, 'wb') as out_f:
        _write_header(header_root, out_f)

        for tu in tu_stream:
            if tu is None:
                continue
            out_f.write(etree.tostring(tu, encoding='utf-8'))
            tu_count += 1

        _write_footter(out_f)

    return tu_count

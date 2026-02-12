"""Writing utilities (streaming)."""

import logging
import os
import tempfile
import time
import warnings
from collections import OrderedDict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import BinaryIO, Callable, Iterable

import lxml.etree as etree

from tmxkit.core.models import TMXHeader


def is_tmx_header(elem: etree.Element) -> bool:
    """Return True if ``elem`` is a TMX ``<header>`` element."""
    q = etree.QName(elem)
    if q.localname != 'header':
        return False
    parent = elem.getparent()
    return parent is not None and etree.QName(parent).localname == 'tmx'


def make_default_header() -> etree.Element:
    """Create a default ``<header>`` element containing tmxkit version info."""
    # TODO ヘッダインスタンス作成に変更する
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

    # <header> を書き出す
    out_f.write(etree.tostring(header, encoding='utf-8'))

    # body の開始タグを書き出す
    out_f.write(b'<body>\n')


def _write_footer(out_f: BinaryIO) -> None:
    """Write the TMX footer (closing body and tmx tags)."""
    out_f.write(b'</body>\n')
    out_f.write(b'</tmx>\n')


def write_tu_stream(
    tu_stream: Iterable[etree.Element],
    out_path: Path,
    header_path: Path | None = None,
    header_obj: TMXHeader | None = None,
) -> int:
    """Write a TMX file from a stream of `<tu>` elements.

    Parameters
    ----------
    tu_stream : Iterable[etree.Element]
        An iterator of TU elements.
    header_path : pathlib.Path or None
        Path to a TMX file whose ``<header>`` should be used for output.
        If ``None``, a default header is used.
    header_obj : TMXHeader or None
        Optional ``TMXHeader`` instance to use directly for output. If
        provided, this takes precedence over ``header_path``.
    out_path : pathlib.Path
        Destination file path for the output TMX.

    Returns
    -------
    int
        Number of TUs written.
    """
    # Delegate to TMXWriter for incremental/buffered writing.
    writer = TMXWriter(
        path=out_path,
        header_path=header_path,
        header_obj=header_obj
    )
    try:
        for tu in tu_stream:
            if tu is None:
                continue
            writer.append(tu)
    finally:
        writer.finalize()

    return writer.count


def init_tmx_file(path: Path, header: etree.Element | None = None) -> None:
    """Write TMX prolog and opening `<body>` to ``path``.

    Parameters
    ----------
    path : pathlib.Path
        Destination file path.
    header : etree.Element or None
        Header element to use for the output; if ``None``, a default
        header will be created.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as out_f:
        _write_header(header, out_f)


def append_tu_bytes(path: Path, data: bytes) -> None:
    """Append TU bytes to the specified file.

    Parameters
    ----------
    path : pathlib.Path
        Destination file path.
    data : bytes
        Byte sequence to append (typically ``etree.tostring(tu, encoding='utf-8')``).
    """
    with open(path, 'ab') as out_f:
        out_f.write(data)
        out_f.flush()


def finalize_tmx_file(path: Path) -> None:
    """Write TMX footer (closing tags) to the specified file.

    Parameters
    ----------
    path : pathlib.Path
        Target file path.
    """
    with open(path, 'ab') as out_f:
        _write_footer(out_f)


class TMXWriter:
    """Writer for appending TUs to a single TMX output file.

    Parameters
    ----------
    path : pathlib.Path
        Destination file path.
    header_path : pathlib.Path | None
        Path to a TMX file providing the `<header>` for output. If ``None``,
        a default header will be used.
    buffer_size : int
        Internal buffer threshold (number of TUs) before flushing to disk.
    """

    def __init__(
        self, path: Path,
        header_path: Path | None = None,
        header_obj: TMXHeader | None = None,
        buffer_size: int = 200,
        logger: logging.Logger | None = None
    ):
        """Initialize the TMXWriter.

        Parameters
        ----------
        path : pathlib.Path
            Destination file path.
        header_path : pathlib.Path | None
            Path to a TMX file providing the ``<header>``. If ``None``, a
            default header will be used.
        header_obj : TMXHeader | None
            Optional ``TMXHeader`` instance to use directly for output.
            If provided, this takes precedence over ``header_path``.
        buffer_size : int
            Internal buffer threshold (number of TUs) before flushing.
        logger : logging.Logger | None
            Optional logger instance.
        """
        self.path = Path(path)
        self._header_path = Path(header_path) if header_path is not None else None
        self._header_obj = header_obj
        self.header: etree.Element | None = None
        self.buffer_size = int(buffer_size)
        self._buffer: list[bytes] = []
        self._initialized = False
        self._finalized = False
        self._count = 0
        self.logger = logger or logging.getLogger(__name__)

    def _ensure_init(self) -> None:
        """Ensure writer is initialized (create file and write header)."""
        if not self._initialized:
            # resolve header element from path if provided
            if self._header_path is not None:
                try:
                    from ..io.utils import get_header_xml
                    self.header = get_header_xml(self._header_path)
                except Exception:
                    # fallback to None -> default header
                    self.header = None
            if self._header_obj is not None:
                self.header = self._header_obj.generate_xtm
            else:
                self.header = None

            init_tmx_file(self.path, self.header)
            self._initialized = True

    def append(self, tu: etree.Element) -> None:
        """Append a TU element to the internal buffer.

        If the buffer reaches `buffer_size` the buffer is flushed to disk.
        """
        if self._finalized:
            raise RuntimeError('attempt to append to finalized writer')

        self._ensure_init()
        # 遅延 import で循環を避ける
        from .serializer import serialize_tu
        data = serialize_tu(tu)
        self._buffer.append(data)
        self._count += 1

        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush the internal buffer to disk atomically."""
        if not self._buffer:
            return

        data = b''.join(self._buffer)
        tmp_fd, tmp_path = tempfile.mkstemp(prefix=self.path.name + '.', dir=str(self.path.parent))
        os.close(tmp_fd)

        try:
            if self.path.exists():
                with open(self.path, 'rb') as f:
                    existing = f.read()
            else:
                existing = b''

            with open(tmp_path, 'wb') as tf:
                tf.write(existing)
                tf.write(data)

            os.replace(tmp_path, str(self.path))
            self._buffer = []
        except Exception:
            ts = int(time.time())
            failed = self.path.with_name(self.path.name + f'.failed-{ts}')
            try:
                os.replace(tmp_path, str(failed))
            except Exception:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            self.logger.exception('flush failed for %s, moved to %s', self.path, failed)
            raise

    def finalize(self) -> None:
        """Write footer and finalize the output file."""
        if self._finalized:
            return
        try:
            self.flush()
        finally:
            try:
                finalize_tmx_file(self.path)
            except Exception:
                self.logger.exception('failed to write footer for %s', self.path)
            self._finalized = True

    def close(self) -> None:
        """Close the writer (alias for ``finalize()``)."""
        self.finalize()

    @property
    def count(self) -> int:
        """Return the total number of TUs written."""
        return self._count


class WriterRouter:
    """Router that manages `Path -> TMXWriter` mapping with LRU eviction.

    Controls the number of open writers via ``max_writers``.
    """

    def __init__(
        self,
        writer_factory: Callable[[Path], TMXWriter],
        max_writers: int = 100
    ):
        """Initialize the router.

        Parameters
        ----------
        writer_factory : Callable[[Path], TMXWriter]
            Factory to create `TMXWriter` instances for a given path.
        max_writers : int
            Maximum number of concurrently open writers.
        """
        self.writer_factory = writer_factory
        self.max_writers = int(max_writers)
        self._map: OrderedDict[Path, TMXWriter] = OrderedDict()

    def get_or_create(self, out_path: Path) -> TMXWriter:
        """Get or create a `TMXWriter` for ``out_path``.

        If the router has reached ``max_writers`` the least-recently-used
        writer is finalized and closed.
        """
        out_path = Path(out_path)
        writer = self._map.get(out_path)
        if writer is not None:
            self._map.move_to_end(out_path)
            return writer

        if self.max_writers and len(self._map) >= self.max_writers:
            oldest_path, oldest_writer = self._map.popitem(last=False)
            try:
                oldest_writer.finalize()
            except Exception:
                pass

        writer = self.writer_factory(out_path)
        self._map[out_path] = writer
        return writer

    def flush_all(self) -> None:
        """Flush all managed writers."""
        for writer in list(self._map.values()):
            try:
                writer.flush()
            except Exception:
                pass

    def close_all(self) -> None:
        """Close all managed writers and clear the router."""
        for writer in list(self._map.values()):
            try:
                writer.close()
            except Exception:
                pass
        self._map.clear()


def _sanitize_filename(name: str) -> str:
    import re
    name = (name or '').strip()
    return re.sub(r'[^0-9A-Za-z._-]', '_', name)


def default_output_resolver(key: str, ext: str = '.tmx') -> Path:
    """Default resolver that maps a classification key to an output Path."""
    safe = _sanitize_filename(key)
    return Path(f'{safe}{ext}')


def default_writer_factory(
    base_dir: Path,
    header_path: Path | None = None,
    header_obj: TMXHeader | None = None,
    buffer_size: int = 200
) -> Callable[[Path], TMXWriter]:
    """Return a default factory function that produces ``TMXWriter`` instances.

    The returned factory will resolve relative output paths against ``base_dir``.

    Parameters
    ----------
    base_dir : pathlib.Path
        ベースディレクトリ。出力パスが相対の場合に結合される。
    header_path : pathlib.Path | None
        ヘッダを持つ TMX ファイルのパス（None の場合はデフォルトヘッダ）。
    header_obj : TMXHeader | None
        出力 TMX のヘッダ情報を直接指定する場合の `TMXHeader` インスタンス。
        `None` の場合は `header_path` を使用する。
    buffer_size : int
        Internal buffer threshold (number of TUs) for created ``TMXWriter``.
    """
    def factory(out_path: Path) -> TMXWriter:
        p = Path(out_path)
        if not p.is_absolute():
            p = Path(base_dir) / p
        return TMXWriter(p, header_path=header_path, header_obj=header_obj, buffer_size=buffer_size)

    return factory

"""Writing out a single stream"""
from __future__ import annotations

import logging
import time
import warnings
from collections import OrderedDict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import BinaryIO, Callable, Iterable

import lxml.etree as etree

from tmxkit.core.models import TMXHeader

logger = logging.getLogger(__name__)

_FOOTER_BYTES = b'</body>\n</tmx>\n'


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

    # <tmx> ルートが渡された場合は子要素の header を探す。
    # 単独の <header> 要素はそのまま使う。
    if header is not None:
        localname = etree.QName(header).localname
        if localname == 'tmx':
            header = header.find('header')
        elif localname != 'header':
            warnings.warn(
                '⚠️ The header argument is not a TMX header. '
                'Recommended code:\n'
                'import tmxkit\n'
                'header = tmxkit.io.reader.parse_header(input_path).generate_xtm\n',
                category=DeprecationWarning,
                stacklevel=2,
            )
            header = None

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
    error_path: Path | None = None,
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
        Destination file path.
    error_path : pathlib.Path or None
        File path for saving TUs that failed to write on error.
        If ``None``, ``{out_path.stem}_error.tmx`` is auto-generated.

    Returns
    -------
    int
        Number of TUs written.
    """
    # Delegate to TMXWriter for incremental/buffered writing.
    writer = TMXWriter(
        path=out_path,
        header_path=header_path,
        header_obj=header_obj,
        error_path=error_path,
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


def _remove_tmx_footer(path: Path) -> bool:
    """Remove the TMX footer (</body></tmx>) from an existing file, putting it into append mode.

    If the file exists and already ends with the footer, remove it and
    return True. Returns False if the file doesn't exist or has no footer.

    Parameters
    ----------
    path : pathlib.Path
        Target file path.

    Returns
    -------
    bool
        True if the footer was removed, False otherwise.
    """
    if not path.exists():
        return False

    try:
        with open(path, 'rb') as f:
            content = f.read()

        # ファイルの末尾がフッタで終わっているかチェック
        if content.endswith(_FOOTER_BYTES):
            # フッタを削除
            new_content = content[:-len(_FOOTER_BYTES)]
            with open(path, 'wb') as f:
                f.write(new_content)
            return True
    except Exception:
        logger.exception('failed to remove footer from %s', path)

    return False


class TMXWriter:
    """Writer for appending TUs to a single TMX output file.

    In addition to `path`, the constructor accepts a way to specify the
    header: either `header_path` (a path to an existing TMX file to read
    the header from) or `header_obj` (a `TMXHeader` instance).

    Parameters
    ----------
    path : pathlib.Path
        Destination file path.
    header_path : pathlib.Path | None
        Path to a TMX file whose header should be used for output. If None,
        a default header is used.
    header_obj : TMXHeader | None
        A `TMXHeader` instance to directly specify the output TMX's header
        information. If `None`, `header_path` is used instead.
    buffer_size : int
        Internal buffer threshold (number of TUs).
    error_path : pathlib.Path | None
        File path for saving TUs that failed to write on error.
        If ``None``, ``{output filename stem}_error.tmx`` is auto-generated.
    retry_count : int
        Number of retries on write failure. Default is 3.
    retry_delay : float
        Wait time between retries, in seconds. Default is 1.0 second.
    """

    def __init__(
        self, path: Path,
        header_path: Path | None = None,
        header_obj: TMXHeader | None = None,
        buffer_size: int = 200,
        error_path: Path | None = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
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
            Internal buffer threshold (number of TUs).
        error_path : pathlib.Path | None
            File path for saving TUs that failed to write on error.
            If ``None``, ``{output filename stem}_error.tmx`` is auto-generated.
        retry_count : int
            Number of retries on write failure. Default is 3.
        retry_delay : float
            Wait time between retries, in seconds. Default is 1.0 second.
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
        self._error_path = Path(error_path) if error_path is not None else None
        self._retry_count = int(retry_count)
        self._retry_delay = float(retry_delay)
        self._error_initialized = False
        self._error_count = 0

    def _ensure_init(self) -> None:
        """Initialize if not already initialized.

        For a new file, writes the header + body opening tag. For an
        existing file, to put it into append mode, strips the trailing
        footer (the footer is rewritten by finalize()).
        """
        if not self._initialized:
            # header_obj 優先、なければ header_path から解決する
            if self._header_obj is not None:
                self.header = self._header_obj.generate_xtm
            elif self._header_path is not None:
                try:
                    from ..io.utils import get_header_xml
                    self.header = get_header_xml(self._header_path)
                except Exception:
                    # fallback to None -> default header
                    logger.exception(
                        'failed to read header from %s, using default header',
                        self._header_path,
                    )
                    self.header = None
            else:
                self.header = None

            if not self.path.exists():
                init_tmx_file(self.path, self.header)
            else:
                # 追記モード: 既存フッタを剥がして開いたままの状態にする
                _remove_tmx_footer(self.path)

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

    def _default_error_path(self) -> Path:
        """Return the default path for the error file."""
        return self.path.with_name(self.path.stem + '_error' + self.path.suffix)

    def _save_failed_to_error(self, data: bytes) -> None:
        """Append TU data that permanently failed to write to the error file."""
        error_path = self._error_path \
            if self._error_path is not None else self._default_error_path()
        try:
            if not self._error_initialized:
                if error_path.exists():
                    # 共有 error_path で先行ライターの退避分を消さないため、
                    # 既存ファイルは初期化せずフッタだけ剥がして追記する
                    _remove_tmx_footer(error_path)
                else:
                    init_tmx_file(error_path, self.header)
                self._error_initialized = True
            append_tu_bytes(error_path, data)
            logger.warning('failed TUs saved to error file: %s', error_path)
        except Exception:
            logger.exception('failed to save error TUs to %s', error_path)

    def flush(self) -> None:
        """Flush the internal buffer to disk.

        Performs a simple append only, without rereading the whole existing
        file (O(1) I/O). Since `_ensure_init` has already stripped the
        footer, the file being written to is left in an "open" state
        without a footer (the footer is written by finalize()).
        If writing fails, retries up to ``retry_count`` times.
        If all retries fail, saves the failed TUs to the error file.
        """
        if not self._buffer:
            return

        data = b''.join(self._buffer)

        for attempt in range(self._retry_count + 1):
            try:
                append_tu_bytes(self.path, data)
                self._buffer = []
                return
            except Exception:
                if attempt < self._retry_count:
                    logger.warning(
                        'flush failed for %s (attempt %d/%d), retrying in %.1fs',
                        self.path, attempt + 1, self._retry_count + 1, self._retry_delay,
                    )
                    time.sleep(self._retry_delay)
                else:
                    logger.exception(
                        'flush permanently failed for %s after %d retries, saving to error file',
                        self.path, self._retry_count,
                    )

        self._save_failed_to_error(data)
        self._error_count += len(self._buffer)
        self._buffer = []

    def finalize(self) -> None:
        """Write the footer to finalize the file. Also finalizes the error file if one exists.

        Because of append mode, the file has no footer while being written
        to. If finalize() is never called due to a crash or similar, a
        footer-less file remains, but it can be repaired afterward with
        `finalize_tmx_file`.
        """
        if self._finalized:
            return
        try:
            # 空ストリームでも有効な TMX（ヘッダ + 空 body）を出力する
            self._ensure_init()
            self.flush()
        finally:
            try:
                finalize_tmx_file(self.path)
            except Exception:
                logger.exception('failed to write footer for %s', self.path)
            if self._error_initialized:
                error_path = self._error_path \
                    if self._error_path is not None else self._default_error_path()
                try:
                    # 共有 error_path で他ライターが先に finalize 済みでも
                    # 二重フッタにならないようにする
                    _remove_tmx_footer(error_path)
                    finalize_tmx_file(error_path)
                except Exception:
                    logger.exception('failed to write footer for error file %s', error_path)
            self._finalized = True

    def close(self) -> None:
        """Close the writer (alias for ``finalize()``)."""
        self.finalize()

    @property
    def count(self) -> int:
        """Return the total number of TUs written to the main file (excluding those saved to the error file)."""
        return self._count - self._error_count

    @property
    def error_count(self) -> int:
        """Return the total number of TUs saved to the error file."""
        return self._error_count


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
    buffer_size: int = 200,
    error_path: Path | None = None,
) -> Callable[[Path], TMXWriter]:
    """Return a default factory function that produces ``TMXWriter`` instances.

    The returned factory will resolve relative output paths against ``base_dir``.

    Parameters
    ----------
    base_dir : pathlib.Path
        Base directory. Joined with the output path when it is relative.
    header_path : pathlib.Path | None
        Path to a TMX file with a header (default header if None).
    header_obj : TMXHeader | None
        A `TMXHeader` instance to directly specify the output TMX's header
        information. If `None`, `header_path` is used instead.
    buffer_size : int
        Internal buffer size of the TMXWriter.
    error_path : pathlib.Path | None
        File path for saving TUs that failed to write on error.
        If ``None``, each writer uses its own auto-generated path.
    """
    def factory(out_path: Path) -> TMXWriter:
        p = Path(out_path)
        if not p.is_absolute():
            p = Path(base_dir) / p
        return TMXWriter(
            p,
            header_path=header_path,
            header_obj=header_obj,
            buffer_size=buffer_size,
            error_path=error_path,
        )

    return factory

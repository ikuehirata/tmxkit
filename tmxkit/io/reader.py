"""Reading (stream)"""
from __future__ import annotations

import copy
import io
from pathlib import Path
from typing import Iterator

import lxml.etree as etree

from ..core.models import TU, TMXHeader, Tuv
from ..errors import StreamError, TmxParseError


def parse_header(path: Path) -> TMXHeader:
    """Read the ``<header>`` element from a TMX file and return a ``TMXHeader``.

    This is a thin helper around ``TMXHeader.from_tmx_file`` for convenience.
    """
    header = TMXHeader.from_tmx_file(path)
    return header


def _parse_tuv(seg_elem: etree.Element, lang: str | None = None) -> Tuv:
    """Parse a TMX `<seg>` element and convert it to a Tuv.

    Parameters
    ----------
    seg_elem : etree.Element
        TMX `<seg>` element.
    lang : str | None
        Language code.

    Returns
    -------
    Tuv
        The parsed TUV.
    """
    text = ''.join(seg_elem.itertext()).strip()
    return Tuv(
        text=text,
        lang=lang,
        raw_xml=seg_elem,
    )


def _parse_tu(tu_elem: etree.Element, order: int = 0) -> TU:
    """Parse a TMX `<tu>` element and convert it to a TU.

    Parameters
    ----------
    tu_elem : etree.Element
        TMX `<tu>` element.
    order : int
        Order of appearance in the original file.

    Returns
    -------
    TU
        The parsed TU.
    """
    change_date = tu_elem.attrib.get('changedate')
    creation_date = tu_elem.attrib.get('creationdate')
    creation_id = tu_elem.attrib.get('creationid')
    change_id = tu_elem.attrib.get('changeid')

    tuvs: dict[str, Tuv] = {}
    props: dict = {}

    # <tuv> 要素ごとにセグメントを抽出
    for tuv_elem in tu_elem.findall('tuv'):
        lang = tuv_elem.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
        if not lang:
            lang = tuv_elem.attrib.get('lang')

        # <seg> を探す
        seg_elem = tuv_elem.find('seg')
        if seg_elem is not None:
            tuv = _parse_tuv(seg_elem, lang=lang)
            if lang:
                tuvs[lang] = tuv

    # <prop> 要素を抽出
    for prop_elem in tu_elem.findall('prop'):
        ptype = prop_elem.attrib.get('type')
        ptext = prop_elem.text or ''
        if ptype:
            props[ptype] = ptext

    # ソース言語・ターゲット言語は最初と2番目のセグメントから推測
    # または props から取得
    source_lang = None
    target_lang = None

    lang_list = list(tuvs.keys())
    if len(lang_list) >= 1:
        source_lang = lang_list[0]
    if len(lang_list) >= 2:
        target_lang = lang_list[1]

    return TU(
        tuvs=tuvs,
        source_lang=source_lang,
        target_lang=target_lang,
        props=props,
        change_date=change_date,
        creation_date=creation_date,
        creation_id=creation_id,
        change_id=change_id,
        order=order,
        raw_xml=tu_elem,
    )


def _check_root_is_tmx(input_file: str | Path) -> None:
    """Verify in advance that the root element is `<tmx>`.

    `iterparse` with `recover=True` silently returns only the first element
    without raising an exception, even for broken XML with multiple top-level
    elements. So we validate the root tag before starting the actual
    processing, to detect fragment files being passed in by mistake.
    """
    try:
        context = etree.iterparse(
            str(input_file), events=('start',), recover=True, huge_tree=True)
        _event, root_elem = next(iter(context))
    except StopIteration:
        raise TmxParseError(f'Empty or unparsable file: {input_file}') from None
    except etree.XMLSyntaxError as e:
        raise TmxParseError(f'Failed to parse as TMX: {input_file}') from e

    localname = etree.QName(root_elem).localname
    if localname != 'tmx':
        raise TmxParseError(
            f'Root element is not <tmx> (found <{localname}>): {input_file}. '
            'If this is a fragment file with multiple top-level <tu> elements, '
            'use stream_tu_fragment() instead.'
        )


def stream_tu(
    input_file: str | Path,
    parse: bool = False,
) -> Iterator[etree.Element | TU]:
    """Generator that sequentially returns TU elements from a TMX file.

    Parameters
    ----------
    input_file : str | Path
        Input file path. Expected to be a valid TMX file with a `<tmx>` root.
    parse : bool, optional
        If True, returns TU dataclasses. If False, returns etree.Element.
        Default is False.

    Yields
    ------
    etree.Element | TU
        A TU element (etree.Element) or TU dataclass.

    Notes
    -----
    - To avoid pressuring memory when handling large TMX files, this
      processes sequentially with `iterparse` and releases each element
      with `elem.clear()` after yielding. Because of this, an `etree.Element`
      returned with `parse=False` becomes empty on the next iteration (use it
      only in a non-retaining fashion). With `parse=True`, a `deepcopy`d
      element is used internally, so the returned `TU` (and
      `TU.raw_xml` / `Tuv.raw_xml`) can be safely retained.
    - Fragment files that have no root element and consist only of a
      sequence of top-level `<tu>` elements cannot be parsed by this
      generator. Use `stream_tu_fragment` instead.
    """
    _check_root_is_tmx(input_file)

    try:
        order = 0
        # 正常な TMX ファイルとして逐次パースする
        for _event, elem in etree.iterparse(
                str(input_file),
                events=('end',),
                tag='tu',
                recover=True,
                huge_tree=True,
        ):
            if parse:
                # clear() で消える前提のため、パース結果は deepcopy 済みの要素に対して作る
                yield _parse_tu(copy.deepcopy(elem), order=order)
            else:
                yield elem

            order += 1

            # 安全な解放
            elem.clear()

            while elem.getprevious() is not None:
                del elem.getparent()[0]

    except etree.XMLSyntaxError as e:
        raise TmxParseError(
            f'Failed to parse as TMX (root <tmx> required): {input_file}. '
            'If this is a fragment file with multiple top-level <tu> elements, '
            'use stream_tu_fragment() instead.'
        ) from e
    except Exception as e:
        raise StreamError(f'Unexpected error while streaming TU from {input_file}') from e


def stream_tu_fragment(
    input_file: str | Path,
    parse: bool = False,
) -> Iterator[etree.Element | TU]:
    """Generator that sequentially returns TU elements from a TU fragment file with no root element.

    This API is for reading files that are not valid XML on their own,
    such as `<tu>...</tu><tu>...</tu>` with multiple top-level `<tu>`
    elements. Internally it wraps the content in a `<root>` wrapper before
    calling `iterparse`, so it can be read via streaming (without holding
    the whole DOM in memory), just like `stream_tu`.

    Parameters
    ----------
    input_file : str | Path
        Input file path.
    parse : bool, optional
        If True, returns TU dataclasses. If False, returns etree.Element.
        Default is False.

    Yields
    ------
    etree.Element | TU
        A TU element (etree.Element) or TU dataclass.

    Notes
    -----
    - With `parse=True`, a `deepcopy`d element is parsed just like
      `stream_tu`, so the returned `TU` can be safely retained.
    - For files with a normal `<tmx><body>...</body></tmx>` structure, use
      `stream_tu` instead.
    """
    path = Path(input_file)
    try:
        data = path.read_bytes()
    except Exception as e:
        raise StreamError(f'Unexpected error while reading: {input_file}') from e

    wrapped = io.BytesIO(b'<root>' + data + b'</root>')

    try:
        order = 0
        for _event, elem in etree.iterparse(
                wrapped,
                events=('end',),
                tag='tu',
                recover=True,
                huge_tree=True,
        ):
            if parse:
                yield _parse_tu(copy.deepcopy(elem), order=order)
            else:
                yield elem

            order += 1

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

    except etree.XMLSyntaxError as e:
        raise TmxParseError(f'Failed to parse TU fragment file: {input_file}') from e
    except Exception as e:
        raise StreamError(f'Unexpected error while streaming TU from {input_file}') from e

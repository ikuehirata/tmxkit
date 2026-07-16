"""Dataclass module representing the TMX `<header>` and `<tu>` elements.

This module provides dataclasses corresponding to the TMX `<header>` and
`<tu>` elements, holding required and optional attributes as fields.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import lxml.etree as etree

logger = logging.getLogger(__name__)


def _tmxkit_version() -> str:
    """Return the tmxkit version string. Returns 'unknown' if not installed."""
    try:
        return version('tmxkit')
    except PackageNotFoundError:
        return 'unknown'


@dataclass
class TMXHeader:
    """Dataclass for the TMX ``<header>`` element.

    See: https://www.ttt.org/oscarStandards/tmx/tmx13.htm#references

    Attributes
    ----------
    creationtool : str
        Name of the tool that created the TMX. Required.
    creationtoolversion : str
        Version of the creation tool. Required.
    segtype : str
        Segment type. Required.
    o_tmf : str
        Original TM format identifier (``o-tmf`` attribute). Required.
    adminlang : str
        Administrative language. Required.
    srclang : str
        Source language. Required.
    datatype : str
        Data type. Required.
    tgtlang : str | None
        Target language. Required; must be set explicitly. Default is None.
        `from_tmx_file` leaves it as None and emits a warning if the
        targetlang prop is missing.
    o_encoding : str | None, optional
        Original file encoding (``o-encoding`` attribute). Default ``None``.
    creationdate : str | None, optional
        Creation date string. Default ``None``.
    creationid : str | None, optional
        Creator identifier. Default ``None``.
    changedate : str | None, optional
        Last change date. Default ``None``.
    changeid : str | None, optional
        Last change author ID. Default ``None``.
    props : dict
        Dictionary of optional ``<prop>`` elements. Default empty dict.
    """

    creationtool: str = 'tmxkit'
    creationtoolversion: str = field(default_factory=_tmxkit_version)
    segtype: str = ''
    o_tmf: str = ''
    adminlang: str = ''
    srclang: str = ''
    datatype: str = ''
    tgtlang: str | None = None

    o_encoding: str | None = None
    creationdate: str | None = None
    creationid: str | None = None
    changedate: str | None = None
    changeid: str | None = None

    props: dict = field(default_factory=dict)

    @classmethod
    def from_element(cls, header: etree.Element) -> 'TMXHeader':
        """Create a ``TMXHeader`` instance from a ``<header>`` element.

        Parameters
        ----------
        header : etree.Element
            The TMX ``<header>`` element.

        Returns
        -------
        TMXHeader
            The created ``TMXHeader`` instance.
        """
        if header is None:
            raise ValueError('header element is required')

        data = {
            'creationtool': header.get('creationtool', '') or '',
            'creationtoolversion': header.get('creationtoolversion', '') or '',
            'segtype': header.get('segtype', '') or '',
            'o_tmf': header.get('o-tmf', '') or '',
            'adminlang': header.get('adminlang', '') or '',
            'srclang': header.get('srclang', '') or '',
            'datatype': header.get('datatype', '') or '',
            'o_encoding': header.get('o-encoding') or None,
            'creationdate': header.get('creationdate') or None,
            'creationid': header.get('creationid') or None,
            'changedate': header.get('changedate') or None,
            'changeid': header.get('changeid') or None,
            'props': {},
        }

        for prop in header.findall('prop'):
            ptype = prop.get('type')
            if not ptype:
                continue
            ptext = prop.text if prop.text is not None else ''
            data['props'][ptype] = ptext
            if ptype == 'targetlang':
                data['tgtlang'] = ptext

        # dataから空要素を除く
        new_data = {k: v for k, v in data.items() if v is not None and v != ''}

        return cls(**new_data)

    @classmethod
    def from_tmx_file(cls, tmx_path: Path) -> 'TMXHeader':
        """Helper that reads the `<header>` from a TMX file path and builds a `TMXHeader`."""
        from ..io.utils import get_header_xml  # 遅延インポート（循環インポート回避）

        header = get_header_xml(tmx_path)
        if header is None:
            raise ValueError(f'No <header> found in TMX file: {tmx_path}')

        instance = cls.from_element(header)

        # targetlang prop が無い TMX は暗黙のデフォルト（旧: 'ja'）にせず、
        # None のまま返して警告を残す
        if instance.tgtlang is None:
            logger.warning(
                'targetlang prop not found in TMX header: %s (tgtlang is None)',
                tmx_path,
            )

        return instance

    @property
    def generate_xtm(self) -> etree.Element:
        """Return an ``etree.Element`` representing the TMX ``<header>``.

        Returns
        -------
        etree.Element
            The ``<header>`` element. Keys from ``props`` are written to the
            ``type`` attribute of child ``<prop>`` elements and their values
            become the element text.
        """
        header = etree.Element('header')

        # 必須属性
        header.set('creationtool', self.creationtool)
        header.set('creationtoolversion', self.creationtoolversion)
        header.set('segtype', self.segtype)
        header.set('o-tmf', self.o_tmf)
        header.set('adminlang', self.adminlang)
        header.set('srclang', self.srclang)
        header.set('datatype', self.datatype)

        # 任意属性（存在する場合のみ設定）
        if self.o_encoding:
            header.set('o-encoding', self.o_encoding)
        if self.creationdate:
            header.set('creationdate', self.creationdate)
        if self.creationid:
            header.set('creationid', self.creationid)
        if self.changedate:
            header.set('changedate', self.changedate)
        if self.changeid:
            header.set('changeid', self.changeid)

        # props は type 属性をキー、テキストを値として子要素を作成する
        # 既に props に 'targetlang' がない場合は `tgtlang` を追加する
        props = dict(self.props) if self.props is not None else {}
        if 'targetlang' not in props and getattr(self, 'tgtlang', None):
            props['targetlang'] = self.tgtlang

        for key, val in props.items():
            prop_el = etree.SubElement(header, 'prop')
            prop_el.set('type', key)
            prop_el.text = '' if val is None else str(val)

        return header


@dataclass
class Tuv:
    """Dataclass representing a TMX TUV (per-language variant of a translation unit).

    Corresponds to the TMX `<tuv>` element.

    Attributes
    ----------
    text : str
        The segment's text content.
    lang : str | None
        Language code (xml:lang attribute).
    raw_xml : etree.Element | None
        The raw XML element, kept as a fallback for full reconstruction.
    """

    text: str
    '''The segment's text content.'''
    lang: str | None = None
    '''Language code (xml:lang attribute).'''
    raw_xml: etree.Element | None = None
    '''The raw XML element, kept as a fallback for full reconstruction.'''

    def is_empty(self) -> bool:
        """Whether the text is empty."""
        return not self.text.strip()


@dataclass
class TU:
    """Dataclass representing a TMX `<tu>` element (Translation Unit).

    Attributes
    ----------
    tuvs : dict[str, Tuv]
        Dictionary keyed by language code with Tuv values.
        Typically 'ja', 'en', etc.
    source_lang : str | None
        Source language code.
    target_lang : str | None
        Target language code.
    props : dict
        Dictionary of TMX `<prop>` elements.
    change_date : str | None
        Last change datetime (changedate attribute).
    creation_date : str | None
        Creation datetime (creationdate attribute).
    order : int
        Order of appearance in the original file.
    raw_xml : etree.Element | None
        The raw XML element, kept as a fallback for full reconstruction.
    """

    tuvs: dict[str, Tuv] = field(default_factory=dict)
    '''Dictionary keyed by language code with Tuv values.'''
    source_lang: str | None = None
    '''Source language code.'''
    target_lang: str | None = None
    '''Target language code.'''
    props: dict = field(default_factory=dict)
    '''Dictionary of TMX `<prop>` elements.'''
    change_date: str | None = None
    '''Last change datetime (changedate attribute).'''
    creation_date: str | None = None
    '''Creation datetime (creationdate attribute).'''
    creation_id: str | None = None
    '''Creator ID (creationid attribute).'''
    change_id: str | None = None
    '''Last change author ID (changeid attribute).'''
    order: int = -1
    '''Order of appearance in the original file.'''
    raw_xml: etree.Element | None = None
    '''The raw XML element, kept as a fallback for full reconstruction.'''

    def get(self, key: str, default: str | None = None) -> str | None:
        """etree.Element-compatible get method. Retrieves an attribute value.

        Parameters
        ----------
        key : str
            Attribute name (TMX attribute name, camelCase).
        default : str | None, optional
            Default value if the attribute doesn't exist. Default is None.

        Returns
        -------
        str | None
            The attribute value, or the default if it doesn't exist.

        Notes
        -----
        This method exists for compatibility with etree.Element's .get()
        method. The key name is automatically mapped to the TU field name.
        """
        attr_map = {
            'changedate': 'change_date',
            'creationdate': 'creation_date',
            'creationid': 'creation_id',
            'changeid': 'change_id',
        }
        field_name = attr_map.get(key, key)
        # 空文字は有効な属性値なので default に化けさせない
        value = getattr(self, field_name, None)
        return value if value is not None else default

    def findall(self, path: str) -> list[etree.Element]:
        """etree.Element-compatible findall method. Searches for sub-elements.

        Parameters
        ----------
        path : str
            XPath path.

        Returns
        -------
        list[etree.Element]
            List of matching elements. Empty list if raw_xml is absent.

        Notes
        -----
        This method exists for compatibility with etree.Element's .findall()
        method. It delegates to the internal raw_xml.
        """
        if self.raw_xml is not None:
            return self.raw_xml.findall(path)
        return []

    def get_source(self) -> Tuv | None:
        """Get the source language segment."""
        if self.source_lang and self.source_lang in self.tuvs:
            return self.tuvs[self.source_lang]
        # source_lang が未指定の場合は最初のセグメントを返す
        if self.tuvs:
            return next(iter(self.tuvs.values()))
        return None

    def get_target(self) -> Tuv | None:
        """Get the target language segment."""
        if self.target_lang and self.target_lang in self.tuvs:
            return self.tuvs[self.target_lang]
        return None

    def has_target(self) -> bool:
        """Whether the target segment exists and is non-empty."""
        seg = self.get_target()
        return seg is not None and not seg.is_empty()

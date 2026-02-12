"""Data classes representing the TMX ``<header>`` element.

This module provides a dataclass corresponding to the TMX ``<header>``
element, exposing required and optional attributes as fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path

import lxml.etree as etree

from ..io.utils import get_header_xml


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
        Target language. Set by the user or inferred.
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
    creationtoolversion: str = version('tmxkit')
    segtype: str = ''
    o_tmf: str = ''
    adminlang: str = ''
    srclang: str = ''
    datatype: str = ''
    tgtlang: str = 'ja'

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
        """Helper to read ``<header>`` from a TMX file path and create a ``TMXHeader`` instance."""
        header = get_header_xml(tmx_path)
        if header is None:
            raise ValueError(f'No <header> found in TMX file: {tmx_path}')

        instance = cls.from_element(header)

        # tgtlang が props にない場合は、tuを1個取り出して調べる
        if instance.tgtlang is None:
            # TODO 未実装
            raise ValueError('targetlang not found in header props')

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

"""Utilities for working with ``<seg>`` / ``<tuv>`` elements."""

import re
from typing import Literal

import lxml.etree as etree

from ..errors import InvalidTUError

SEGMENTS = Literal[
    'source',
    'target',
]

_ALLOWED_SEGMENTS: set[str] = {
    'source',
    'target',
}


def get_segment(tu: etree.Element, lang_code: str) -> etree.Element | None:
    """Return the ``<seg>`` element for the specified language code from a TU.

    Parameters
    ----------
    tu : etree.Element
        The ``<tu>`` element to search.
    lang_code : str
        Language code to match (e.g. 'en', 'ja').

    Returns
    -------
    etree.Element | None
        The matching ``<seg>`` element, or ``None`` if not found.
    """
    if tu is None or not hasattr(tu, 'findall'):
        raise InvalidTUError('get_segment expects a tu element')

    for tuv in tu.findall('tuv'):
        lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
        if lang == lang_code:
            seg = tuv.find('seg')
            if seg is not None:
                return seg
    return None


def get_text(
    segment: etree.Element
) -> str | None:
    """Return the inner XML of a ``<seg>`` element as a string.

    Parameters
    ----------
    segment : etree.Element
        The ``<seg>`` element to extract inner XML from.

    Returns
    -------
    str | None
        The inner XML of the ``<seg>`` element, or ``None`` if the
        provided segment is ``None``.
    """
    # segment が None の場合は None を返す（呼び出し側で処理する）
    if segment is None:
        return None

    # 安全のため seg 全体を文字列化して外側の <seg> タグを剥がす
    seg_str = etree.tostring(segment, encoding='unicode')
    # remove opening <seg ...> and closing </seg>
    inner = re.sub(r'^<seg[^>]*>', '', seg_str)
    inner = re.sub(r'</seg>', '', inner)
    inner = inner.strip()
    return inner


def replace_text(
    segment: etree.Element,
    new_inner_xml: str
) -> etree.Element:
    """Replace the contents of a ``<seg>`` element with new inner XML.

    Parameters
    ----------
    segment : etree.Element
        The ``<seg>`` element to modify.
    new_inner_xml : str
        New XML string to insert inside the ``<seg>`` element.

    Returns
    -------
    etree.Element
        The modified ``<seg>`` element.
    """
    # 既存の中身を全部消す
    segment.clear()

    # ダミールートで包んで再パース
    wrapper = etree.fromstring(f'<wrapper>{new_inner_xml}</wrapper>')

    # text
    segment.text = wrapper.text

    # 子要素
    for child in wrapper:
        segment.append(child)

    return segment

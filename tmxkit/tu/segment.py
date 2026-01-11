"""Utilities for working with ``<seg>`` / ``<tuv>`` elements."""

import re

import lxml.etree as etree

from ..errors import InvalidTUError


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


def get_lang_text(tu: etree.Element, lang_code: str) -> str | None:
    """Get the inner XML text of the ``<seg>`` for the given language code.

    Parameters
    ----------
    tu : etree.Element
        The ``<tu>`` element.
    lang_code : str
        Language code (e.g. 'en', 'ja').

    Returns
    -------
    str | None
        The inner XML of the ``<seg>`` element. Returns ``None`` if the
        requested language is not present.
    """
    seg = get_segment(tu, lang_code)
    if seg is None:
        raise InvalidTUError(f'<seg> not found for lang: {lang_code}')

    # 安全のため seg 全体を文字列化して外側の <seg> タグを剥がす
    seg_str = etree.tostring(seg, encoding='unicode')
    # remove opening <seg ...> and closing </seg>
    inner = re.sub(r'^<seg[^>]*>', '', seg_str)
    inner = re.sub(r'</seg>', '', inner)
    inner = inner.strip()
    return inner


def replace_lang_text(tu: etree.Element, lang_code: str, new_inner_xml: str) -> etree.Element:
    """Replace the contents of the ``<seg>`` for a given language with new XML.

    Parameters
    ----------
    tu : etree.Element
        The ``<tu>`` element.
    lang_code : str
        Language code (e.g. 'en', 'ja').
    new_inner_xml : str
        New XML string to insert inside the ``<seg>`` element.

    Returns
    -------
    etree.Element
        The modified ``<tu>`` element.
    """
    seg = get_segment(tu, lang_code)
    if seg is None:
        raise InvalidTUError(f'<seg> not found for lang: {lang_code}')

    # 既存の中身を全部消す
    seg.clear()

    # ダミールートで包んで再パース
    wrapper = etree.fromstring(f'<wrapper>{new_inner_xml}</wrapper>')

    # text
    seg.text = wrapper.text

    # 子要素
    for child in wrapper:
        seg.append(child)

    return tu

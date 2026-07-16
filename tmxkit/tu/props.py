"""prop operations"""
from __future__ import annotations

import lxml.etree as etree

from ..errors import InvalidTUError


def extract_props(tu: etree.Element) -> dict[str, str]:
    """Extract all ``<prop>`` elements from a ``<tu>`` and return a dict.

    The returned dictionary maps the ``type`` attribute of each ``<prop>``
    to its text content (empty string if none).
    """
    if tu is None or not hasattr(tu, 'findall'):
        raise InvalidTUError('extract_props expects a tu element')

    props = {}
    for prop in tu.findall('prop'):
        t = prop.get('type')
        if t:
            props[t] = (prop.text or '')
    return props


def get_prop_value(tu: etree.Element, prop_type: str, ignore_linebreak=True) -> str | None:
    """Return the value of a named ``<prop>`` within a ``<tu>``.

    If ``ignore_linebreak`` is True, line breaks are removed from the
    returned value.
    """
    if tu is None or not hasattr(tu, 'findall'):
        raise InvalidTUError('get_prop_value expects a tu element')

    for prop in tu.findall('prop'):
        if prop.get('type') == prop_type:
            # 改行を無視しない場合はそのまま返す
            if not ignore_linebreak:
                return prop.text
            # 改行を無視する場合は改行を削除して返す
            raw_text = etree.tostring(prop, encoding='utf-8', method='text').decode('utf-8')
            raw_text = raw_text.replace('\n', '').replace('\r', '')
            raw_text = raw_text.strip()
            return raw_text
    return None


def replace_prop_value(tu: etree.Element, prop_type: str, new_value: str) -> etree.Element:
    """Replace or create a ``<prop>`` element with the given type/value.

    If a ``<prop>`` with ``type==prop_type`` exists, its text is updated;
    otherwise a new ``<prop>`` element is appended to the ``<tu>``.
    """
    if tu is None or not hasattr(tu, 'findall'):
        raise InvalidTUError('replace_prop_value expects a tu element')

    wrote = False
    # 上書き
    for prop in tu.findall('prop'):
        if prop.get('type') == prop_type:
            prop.text = new_value
            wrote = True
            break

    # prop が見つからなかった場合は新規作成
    if not wrote:
        new_prop = etree.Element('prop', type=prop_type)
        new_prop.text = new_value
        tu.append(new_prop)

    return tu


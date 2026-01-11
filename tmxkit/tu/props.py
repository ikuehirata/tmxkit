"""Utilities for working with ``<prop>`` elements."""

import lxml.etree as etree

from ..errors import InvalidTUError


def extract_props(tu) -> dict[str, str]:
    """Extract ``<prop>`` tags from a ``<tu>`` element and return them as a dict.

    The returned dictionary maps the ``type`` attribute of each ``<prop>`` to
    its text content.
    """
    if tu is None or not hasattr(tu, 'findall'):
        raise InvalidTUError('extract_props expects a tu element')

    props = {}
    for prop in tu.findall('prop'):
        t = prop.get('type')
        if t:
            props[t] = (prop.text or '')
    return props


def get_prop_value(tu, prop_type: str, ignore_linebreak=True) -> str | None:
    """Get the value of a specific ``<prop>`` tag inside a TU.

    Parameters
    ----------
    tu : etree.Element
        The ``<tu>`` element.
    prop_type : str
        The ``type`` attribute value to look for.
    ignore_linebreak : bool, optional
        If True (default), line breaks are removed from the returned value.

    Returns
    -------
    str | None
        The value of the requested ``<prop>`` tag, or ``None`` if not found.
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


def replace_prop_value(tu, prop_type: str, new_value: str) -> etree.Element:
    """Replace or insert a ``<prop>`` tag value inside a TU.

    If a ``<prop>`` with the given ``type`` exists it will be updated; if not,
    a new ``<prop>`` element will be appended to the TU.
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


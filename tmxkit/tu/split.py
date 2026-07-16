"""Utilities to split a TU by ``<ph type="fmt">{}</ph>`` markers.

This module provides a generator that takes a ``<tu>`` element and yields
new TU elements produced by splitting each ``tuv`` on ``<ph type="fmt">{}</ph>``
markers.

Behavior:
- If the number of ``<ph type="fmt">{}</ph>`` markers differs between
    ``tuv`` elements, the original TU is returned unchanged.
- If counts match and are greater than zero, the TU is split into multiple
    TUs according to those markers.
- The marker itself is removed and effectively attached to the end of the
    preceding chunk (not treated as a separator).
"""

from __future__ import annotations

import copy
from typing import Iterator, List

import lxml.etree as etree

from ..errors import InvalidTUError
from .segment import get_text


def _split_inner_by_fmt(seg: etree.Element) -> List[etree.Element]:
    """Parse a ``<seg>`` element and split it by ``<ph type="fmt">{}</ph>``.

    Returns a list of new ``<seg>`` elements. The ``<ph type="fmt">{}</ph>``
    markers are removed from the results.
    """
    if seg is None:
        return [etree.Element('seg')]

    inner_xml = get_text(seg)
    if inner_xml is None:
        return [copy.deepcopy(seg)]

    wrapper_xml = f'<wrapper>{inner_xml}</wrapper>'
    try:
        wrapper = etree.fromstring(wrapper_xml)
    except Exception:
        return [copy.deepcopy(seg)]

    chunks: List[etree.Element] = []
    current_seg = etree.Element('seg')
    current_seg.text = wrapper.text or ''

    for child in wrapper:
        # タグ名は namespace を含む可能性があるため安全に取得する
        try:
            localname = etree.QName(child).localname
        except Exception:
            localname = child.tag if isinstance(child.tag, str) else ''

        is_fmt_ph = (
            localname == 'ph' and
            child.get('type') == 'fmt' and
            (child.text or '').strip() == '{}'
        )

        # 元の子要素から tail テキストを取得する
        tail_text = child.tail or ''

        if is_fmt_ph:
            # fmt ph 要素は追加せず丸ごと削除する
            # 現在のチャンクを確定する（ph は含めない）
            chunks.append(current_seg)
            # tail を初期テキストとして新しい seg を開始する
            current_seg = etree.Element('seg')
            current_seg.text = tail_text
        else:
            # 通常の子要素: tail を除いたコピーを追加し、その後 tail を再接続する
            child_copy = copy.deepcopy(child)
            child_copy.tail = None
            current_seg.append(child_copy)

            if tail_text:
                if len(current_seg):
                    # 最後に追加した子要素に tail を付与する
                    current_seg[-1].tail = (current_seg[-1].tail or '') + tail_text
                else:
                    current_seg.text = (current_seg.text or '') + tail_text

    # 最終チャンク
    if current_seg.text or len(current_seg):
        chunks.append(current_seg)

    return chunks


def split(tu: etree.Element) -> Iterator[etree.Element]:
    """Split a given ``<tu>`` element and yield new ``<tu>`` elements.

    Parameters
    ----------
    tu : etree.Element
        The ``<tu>`` element to split. Expected to be an ``lxml.etree.Element``
        with tag ``'tu'``.

    Yields
    ------
    etree.Element
        New ``<tu>`` elements produced by splitting. On failure or mismatch
        the original ``tu`` is yielded unchanged.
    """
    if tu is None or not hasattr(tu, 'findall'):
        raise InvalidTUError('split expects a tu element')

    tu_tuvs = tu.findall('tuv')
    if not tu_tuvs:
        yield tu
        return

    # 各 tuv について fmt ph の個数と分割チャンクを作成
    fmt_counts: List[int] = []
    all_chunks: List[List[etree.Element]] = []

    for tuv in tu_tuvs:
        seg = tuv.find('seg')
        if seg is None:
            # seg が無ければ分割不能
            yield tu
            return

        chunks = _split_inner_by_fmt(seg)

        # fmt 個数はチャンク数 - 1（0 のときは分割無し）
        fmt_count = max(0, len(chunks) - 1)
        fmt_counts.append(fmt_count)
        all_chunks.append(chunks)

    # 個数が一致しない場合は元TUを返す
    if len(set(fmt_counts)) != 1:
        yield tu
        return

    # 0 個（分割対象なし）の場合は元TUを返す
    if fmt_counts[0] == 0:
        yield tu
        return

    chunk_count = len(all_chunks[0])

    # テンプレ TU を作成（tuv を除いたもの）
    template = copy.deepcopy(tu)
    for child in list(template.findall('tuv')):
        template.remove(child)

    # 各チャンクについて新しい TU を作成
    for i in range(chunk_count):
        new_tu = copy.deepcopy(template)
        # 元の tuv の順序を保って挿入
        for idx, orig_tuv in enumerate(tu_tuvs):
            new_tuv_el = copy.deepcopy(orig_tuv)
            seg = new_tuv_el.find('seg')
            if seg is None:
                # 保守的に元TUを返す
                yield tu
                return

            # all_chunks[idx][i] がこの tuv の i 番目チャンク（etree.Element）
            chunk_seg = all_chunks[idx][i]

            # seg の中身を chunk_seg の内容で置換する（要素操作で文字列化を避ける）
            seg.clear()
            seg.text = chunk_seg.text
            for child in chunk_seg:
                seg.append(copy.deepcopy(child))

            new_tu.append(new_tuv_el)

        yield new_tu


__all__ = ['split']

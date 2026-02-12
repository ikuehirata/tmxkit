"""Orchestration module for preparing TMX segment text.

This module coordinates normalization and tag-processing steps that
prepare segment content for downstream processing.
"""
from __future__ import annotations

from typing import cast

import lxml.etree as etree

from ..core.models import TMXHeader
from .normalize import normalize_whitespace
from .segment import _ALLOWED_SEGMENTS, SEGMENTS, get_segment, get_text, replace_text
from .tags import convert_ph_to_bptept, tagify_plain_html


def run(header: TMXHeader, tu: etree.Element) -> etree.Element:
    """Orchestrate preparation of segment text inside a TU.

    This function applies normalization and tag-processing steps to
    segment content according to the provided `header` information.

    Parameters
    ----------
    header : TMXHeader
        Parsed TMX header providing source/target language information.
    tu : etree.Element
        The `<tu>` element to process.

    Returns
    -------
    etree.Element
        The processed `<tu>` element.
    """
    # srclang, tgtlang を取得
    if header.srclang is None or header.tgtlang is None:
        return tu

    for segment_name in _ALLOWED_SEGMENTS:
        seg_literal = cast(SEGMENTS, segment_name)
        if seg_literal == 'source':
            lang_code = header.srclang.lower()
        else:
            lang_code = header.tgtlang.lower()
        segment = get_segment(tu, lang_code)

        # 元テキスト
        org_text = get_text(segment)
        if org_text is None:
            continue

        # 0) 正規化・軽加工（必要に応じてここで関数を追加）
        normalized = normalize_whitespace(org_text)

        # 1) 平文タグ化
        tagged = tagify_plain_html(normalized)

        # 2) PH -> BPT/EPT 変換
        src_converted = convert_ph_to_bptept(tagged)

        # 置換
        segment = replace_text(segment, src_converted)

    return tu

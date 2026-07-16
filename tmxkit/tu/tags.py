"""Tag processing utilities.

This module contains helper functions to detect and convert HTML-like
tags within segment text into TMX-safe representations used by the toolchain.
"""
from __future__ import annotations

import re
from html import escape
from uuid import uuid4

# ペアタグは開始/終了の両方を処理する。単独タグは開始のみ処理する。
PAIR_TAGS = [
    'a', 'b', 'i', 'u', 'strong', 'em',
    'span', 'div', 'font', 'p',
]
'''Tags with opening and closing pairs'''

SINGLETON_TAGS = [
    'br', 'hr', 'img',
]
'''Singleton (void/singleton) tags'''


def _extract_and_protect_tags(text: str) -> tuple[str, dict[str, str]]:
    """Extract and protect already-tagged portions, replacing them with placeholders.

    Replaces already-tagged markup portions (`<ph>...</ph>`, `<bpt>...</bpt>`,
    etc.) with temporary placeholders, keeping the original values in a
    dict and returning it.

    Parameters
    ----------
    text : str
        The text to process.

    Returns
    -------
    tuple[str, dict[str, str]]
        (text with placeholders substituted in, {placeholder: original value})
    """
    protected: dict[str, str] = {}
    counter = 0
    # 原文にプレースホルダと同じ文字列が含まれても衝突しないよう uuid を混ぜる
    prefix = f'__PROTECTED_TAG_{uuid4().hex}'

    # <ph>...</ph>, <bpt>...</bpt>, <ept>...</ept>, <it>...</it> を抽出
    pattern = re.compile(r'<(ph|bpt|ept|it)(?:\s[^>]*)?>.*?</\1>', re.DOTALL)

    def replace_with_placeholder(match: re.Match) -> str:
        nonlocal counter
        original = match.group(0)
        placeholder = f'{prefix}_{counter}__'
        protected[placeholder] = original
        counter += 1
        return placeholder

    text = pattern.sub(replace_with_placeholder, text)
    return text, protected


def _restore_protected_tags(text: str, protected: dict[str, str]) -> str:
    """Restore placeholders back to their original tags.

    Parameters
    ----------
    text : str
        Text containing placeholders.
    protected : dict[str, str]
        {placeholder: original value}

    Returns
    -------
    str
        The text after restoration.
    """
    for placeholder, original in protected.items():
        text = text.replace(placeholder, original)
    return text



def tagify_canonical_html(text: str) -> str:
    """Convert pseudo-HTML tags like ``[p]``/``[/p]`` into ``ph``-style mq:rxt.

    This function is intended to transform canonical or pseudo-HTML
    bracketed tags into the internal ``<ph>`` representation used by the
    pipeline.
    """
    # TODO 実装
    raise NotImplementedError('tagify_canonical_html is not implemented yet')


def tagify_newline(text: str) -> str:
    r"""Convert line-break characters (\n or literal line breaks) in a string into `ph`-style mq:rxt.

    Already-tagged portions are protected before processing and restored
    afterward.

    Parameters
    ----------
    text : str
        The segment text.

    Returns
    -------
    str
        The converted text.
    """
    # タグ化済み部分を保護
    protected_text, protected = _extract_and_protect_tags(text)

    def _to_ph_from_newline(match_obj: re.Match) -> str:
        # マッチした内容を確認して、リテラル \\n か実改行かを判定
        matched = match_obj.group(1)
        if matched == '\\n':
            # 文字列リテラル \\n
            inner = escape('\\n')
        else:
            # リテラルな改行文字
            inner = escape('\n')
        inner = inner.replace('&quot;', '&amp;quot;')
        return f'<ph>&lt;mq:rxt displaytext="{inner}" val="{inner}" /&gt;</ph>'

    # リテラルな \\n を検出
    protected_text = re.sub(
        r'(\\n)',
        _to_ph_from_newline,
        protected_text,
    )

    # 実際の改行文字を検出
    protected_text = re.sub(
        r'(\n)',
        _to_ph_from_newline,
        protected_text,
    )

    # 保護していたタグを復元
    return _restore_protected_tags(protected_text, protected)


def tagify_plain_html(text: str) -> str:
    """Convert obvious HTML tags into ``ph``-style mq:rxt placeholders.

    Parameters
    ----------
    text : str
        Segment text to process.

    Returns
    -------
    str
        The transformed text with ``<ph>`` placeholders inserted.
    """
    # タグ化済み部分を保護
    protected_text, protected = _extract_and_protect_tags(text)

    def _to_ph_from_raw(raw: str) -> str:
        # raw は '<a href="...">' または '&lt;a href=&quot;...&quot;&gt;' のような形
        # displaytext / val に入れる値は1回だけエスケープする
        inner = escape(raw)
        # inner に '&quot;' が含まれる場合は '&amp;quot;' に置換する
        inner = inner.replace('&quot;', '&amp;quot;')
        return f'<ph>&lt;mq:rxt displaytext="{inner}" val="{inner}" /&gt;</ph>'

    # 単独タグは開始のみ処理
    for t in SINGLETON_TAGS:
        open_literal_re = re.compile(
            rf'(<\s*{t}\b[^>]*>)',
            re.IGNORECASE,
        )
        protected_text = open_literal_re.sub(lambda m: _to_ph_from_raw(m.group(1)), protected_text)

        open_escaped_re = re.compile(
            rf'(&lt;\s*{t}\b.*?&gt;)',
            re.IGNORECASE,
        )
        protected_text = open_escaped_re.sub(lambda m: _to_ph_from_raw(m.group(1)), protected_text)

    # ペアタグは開始/終了の両方を処理
    for t in PAIR_TAGS:
        # opening tag: handle literal <tag ...> first
        open_literal_re = re.compile(
            rf'(<\s*{t}\b[^>]*>)',
            re.IGNORECASE,
        )
        protected_text = open_literal_re.sub(lambda m: _to_ph_from_raw(m.group(1)), protected_text)

        # opening tag: handle escaped &lt;tag ...&gt;
        open_escaped_re = re.compile(
            rf'(&lt;\s*{t}\b.*?&gt;)',
            re.IGNORECASE,
        )
        protected_text = open_escaped_re.sub(lambda m: _to_ph_from_raw(m.group(1)), protected_text)

        # closing tag: literal and escaped
        close_literal_re = re.compile(
            rf'(</\s*{t}\s*>)',
            re.IGNORECASE,
        )
        protected_text = close_literal_re.sub(lambda m: _to_ph_from_raw(m.group(1)), protected_text)

        close_escaped_re = re.compile(
            rf'(&lt;/\s*{t}\s*&gt;)',
            re.IGNORECASE,
        )
        protected_text = close_escaped_re.sub(lambda m: _to_ph_from_raw(m.group(1)), protected_text)

    # 保護していたタグを復元
    return _restore_protected_tags(protected_text, protected)


def find_ph_mq_rxt_tags(text: str) -> list[re.Match]:
    """Return all ``mq:rxt`` elements inside ``<ph>`` tags in order.

    Returns a list of ``re.Match`` objects where the ``displaytext`` value
    is available in group ``'disp'``.
    """
    # ph>&lt;mq:rxt displaytext="&amp;lt;p&amp;gt;" val="&amp;lt;p&amp;gt;" /&gt;</ph>
    pattern = re.compile(r'<ph>\s*&lt;mq:rxt[^>]*displaytext="(?P<disp>.*?)"[^>]*/&gt;\s*</ph>')
    return list(pattern.finditer(text))


def convert_ph_to_bptept(text: str) -> str:
    """Replace mq:rxt representations inside ``<ph>`` with ``bpt``/``ept``.

    This function scans ``<ph>`` elements containing ``mq:rxt`` displaytext
    values and converts matching start/end tag pairs to ``<bpt>``/``<ept>``
    constructs. Unmatched paragraph-like tags are converted to ``<it>``
    with appropriate ``pos`` attribute.
    """
    if '<ph>' not in text:
        return text

    src_matches = list(find_ph_mq_rxt_tags(text))

    def _disp_to_tagname(disp: str) -> str:
        # disp examples: '&amp;lt;b&amp;gt;' or '&amp;lt;/b&amp;gt;'
        if disp.startswith('&amp;amp;lt;') and disp.endswith('&amp;amp;gt;'):
            inner = disp[len('&amp;amp;lt;'):-len('&amp;amp;gt;')]
            return inner
        if disp.startswith('&amp;lt;') and disp.endswith('&amp;gt;'):
            inner = disp[len('&amp;lt;'):-len('&amp;gt;')]
            return inner
        return disp

    def _base_tag(disp: str) -> str:
        """Extract base tag name (lowercased) from a displaytext string.

        Examples:
        - 'a href="..."' -> 'a'
        - '/a' -> 'a'
        - 'p' -> 'p'
        """
        inner = _disp_to_tagname(disp)
        # remove leading slash if present
        inner = inner.lstrip('/')
        m = re.match(r'\s*([A-Za-z0-9]+)', inner)
        if m:
            return m.group(1).lower()
        return inner.lower()

    stack: list[re.Match] = []  # 未対応の開始タグのマッチ
    # 同一文字列の ph が複数あっても一意に置換できるよう位置（span）で持つ
    replacements: list[tuple[int, int, str]] = []  # (start, end, new)
    pair_count = 1

    # build content string placed inside bpt/ept/it (no self-closing slash)
    def _mq_rxt_inner(disp: str, mode: str) -> str:
        # disp contains already-escaped sequences like '&amp;lt;b&amp;gt;'
        if mode == 'open':
            return f'&lt;mq:rxt displaytext="{disp}" val="{disp}"&gt;'
        else:
            return f'&lt;/mq:rxt displaytext="{disp}" val="{disp}"&gt;'

    # iterate matches with position info
    for m in src_matches:
        disp = m.group('disp')
        tagname = _disp_to_tagname(disp)
        is_close = tagname.startswith('/')

        # 基本タグ名を抽出しておく（属性つき 'a href=...' 等を正規化）
        name_base = _base_tag(disp)

        # p は通常通りスタックでペア化を試みるが、
        # マッチする閉じタグがセグメント内に存在しない場合は it に変換する。

        if not is_close:
            # opening tag -> push
            stack.append(m)
        else:
            # closing tag -> try match with stack top
            if stack:
                open_m = stack[-1]
                open_disp = open_m.group('disp')
                open_name_base = _base_tag(open_disp)
                if open_name_base == name_base:
                    stack.pop()
                    # build bpt/ept using the original disp values
                    open_inner = _mq_rxt_inner(open_disp, mode='open')
                    close_inner = _mq_rxt_inner(disp, mode='close')
                    i_val = pair_count
                    bpt = f"<bpt i='{i_val}'>{open_inner}</bpt>"
                    ept = f"<ept i='{i_val}'>{close_inner}</ept>"
                    replacements.append((open_m.start(), open_m.end(), bpt))
                    replacements.append((m.start(), m.end(), ept))
                    pair_count += 1
                else:
                    # 不整合なら、p タグであれば it pos='end' に変換
                    if name_base == 'p':
                        it_inner = _mq_rxt_inner(disp, mode='close')
                        it_tag = f"<it pos='end'>{it_inner}</it>"
                        replacements.append((m.start(), m.end(), it_tag))
                    # それ以外は無視
                    continue
            else:
                # スタック空 -> 閉じタグが未対応。p なら it pos='end' にする
                if name_base == 'p':
                    it_inner = _mq_rxt_inner(disp, mode='close')
                    it_tag = f"<it pos='end'>{it_inner}</it>"
                    replacements.append((m.start(), m.end(), it_tag))
                continue

    # スタックに残った開始タグで未ペアのものは処理する
    for open_m in stack:
        open_disp = open_m.group('disp')
        open_name_base = _base_tag(open_disp)
        if open_name_base == 'p':
            it_inner = _mq_rxt_inner(open_disp, mode='open')
            it_tag = f"<it pos='begin'>{it_inner}</it>"
            replacements.append((open_m.start(), open_m.end(), it_tag))

    # 後ろの位置から順に置換して、前方の span がずれないようにする
    for start, end, new in sorted(replacements, key=lambda r: r[0], reverse=True):
        text = text[:start] + new + text[end:]

    return text

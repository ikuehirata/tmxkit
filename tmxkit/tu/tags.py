"""タグ処理ユーティリティ群。"""
from __future__ import annotations

import re
from html import escape

import lxml.etree as etree

from ..errors import InvalidTUError
from .segment import get_lang_text, replace_lang_text

# 対象タグ群を開閉があるタグと単独（void/singleton）タグに分割
# ペアタグは開始/終了の両方を処理する。単独タグは開始のみ処理する。
PAIR_TAGS = [
    'a', 'b', 'i', 'u', 'strong', 'em',
    'span', 'div', 'font', 'p',
]

SINGLETON_TAGS = [
    'br', 'hr', 'img',
]
# 追加のタグがあれば各リストに追記する


def replace_tags(tu: etree.Element) -> etree.Element:
    """`tu` 内の source/target に対して平文タグ化→PH→BPT/EPT 変換を行う。

    手順:
    1. 指定言語のテキストを取得
    2. `tagify_plain_html` を先に実行して平文タグを `ph` 化
    3. `convert_ph_to_bptept` を適用して `ph` を `bpt`/`ept` に変換
    4. 変換後のテキストで `seg` を置換して返す
    """
    # tu 内の <tuv xml:lang="..."> を読み取り、利用可能な言語コードを検出する
    def _available_langs(tu_elem: etree.Element) -> list[str]:
        langs: list[str] = []
        for tuv in tu_elem.findall('tuv'):
            lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
            if lang:
                langs.append(lang.lower())
        return langs

    def _choose_source_target(langs: list[str]) -> tuple[str | None, str | None]:
        # 優先候補
        src_candidates = ['en-us', 'en']
        tgt_candidates = ['ja', 'ja-jp']

        src = next((c for c in src_candidates if c in langs), None)
        tgt = next((c for c in tgt_candidates if c in langs), None)

        # 部分一致（例: en-GB など）
        if src is None:
            src = next((c for c in langs if c.startswith('en')), None)
        if tgt is None:
            tgt = next((c for c in langs if c.startswith('ja')), None)

        # フォールバック: 2 つ以上の言語があれば順に割り当て
        if src is None or tgt is None:
            if len(langs) >= 2:
                # 既に片方見つかっていれば、もう片方は別言語を採用
                if src is None and tgt is not None:
                    src = next((lang for lang in langs if lang != tgt), None)
                elif tgt is None and src is not None:
                    tgt = next((lang for lang in langs if lang != src), None)
                else:
                    src, tgt = langs[0], langs[1]
            else:
                # 言語が1つしかなければ処理しない
                return None, None

        return src, tgt

    langs = _available_langs(tu)
    source_lang, target_lang = _choose_source_target(langs)
    if source_lang is None or target_lang is None:
        return tu

    try:
        source = get_lang_text(tu, source_lang)
        target = get_lang_text(tu, target_lang)
    except InvalidTUError:
        return tu

    if source is None or target is None:
        return tu

    # 1) 平文タグ化
    src_tagged = tagify_plain_html(source)
    tgt_tagged = tagify_plain_html(target)

    # 2) PH -> BPT/EPT 変換
    src_converted = convert_ph_to_bptept(src_tagged)
    tgt_converted = convert_ph_to_bptept(tgt_tagged)

    # 置換
    tu = replace_lang_text(tu, source_lang, src_converted)
    tu = replace_lang_text(tu, target_lang, tgt_converted)

    return tu


def tagify_plain_html(text: str) -> str:
    """平文に残る明らかな HTML タグ（例: <br>）を `ph` 形式の mq:rxt に変換する。

    Parameters
    ----------
    text : str
        セグメントのテキスト。

    Returns
    -------
    str
        変換後のテキスト。
    """
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
            rf'(?<!<ph>)(?<!<bpt>)(?<!<ept>)(<\s*{t}\b[^>]*>)',
            re.IGNORECASE,
        )
        text = open_literal_re.sub(lambda m: _to_ph_from_raw(m.group(1)), text)

        open_escaped_re = re.compile(
            rf'(?<!<ph>)(?<!<bpt>)(?<!<ept>)(&lt;\s*{t}\b.*?&gt;)',
            re.IGNORECASE,
        )
        text = open_escaped_re.sub(lambda m: _to_ph_from_raw(m.group(1)), text)

    # ペアタグは開始/終了の両方を処理
    for t in PAIR_TAGS:
        # opening tag: handle literal <tag ...> first
        open_literal_re = re.compile(
            rf'(?<!<ph>)(?<!<bpt>)(?<!<ept>)(<\s*{t}\b[^>]*>)',
            re.IGNORECASE,
        )
        text = open_literal_re.sub(lambda m: _to_ph_from_raw(m.group(1)), text)

        # opening tag: handle escaped &lt;tag ...&gt;
        open_escaped_re = re.compile(
            rf'(?<!<ph>)(?<!<bpt>)(?<!<ept>)(&lt;\s*{t}\b.*?&gt;)',
            re.IGNORECASE,
        )
        text = open_escaped_re.sub(lambda m: _to_ph_from_raw(m.group(1)), text)

        # closing tag: literal and escaped
        close_literal_re = re.compile(
            rf'(?<!<ph>)(?<!<bpt>)(?<!<ept>)(</\s*{t}\s*>)',
            re.IGNORECASE,
        )
        text = close_literal_re.sub(lambda m: _to_ph_from_raw(m.group(1)), text)

        close_escaped_re = re.compile(
            rf'(?<!<ph>)(?<!<bpt>)(?<!<ept>)(&lt;/\s*{t}\s*&gt;)',
            re.IGNORECASE,
        )
        text = close_escaped_re.sub(lambda m: _to_ph_from_raw(m.group(1)), text)

    return text


def find_ph_mq_rxt_tags(text: str) -> list[re.Match]:
    """`ph` 内の `mq:rxt` 要素を順序付きで全て返す。

    戻り値は re.Match のリストで、`displaytext` を group 'disp' で取り出せる。
    """
    # ph>&lt;mq:rxt displaytext="&amp;lt;p&amp;gt;" val="&amp;lt;p&amp;gt;" /&gt;</ph>
    pattern = re.compile(r'<ph>\s*&lt;mq:rxt[^>]*displaytext="(?P<disp>.*?)"[^>]*/&gt;\s*</ph>')
    return list(pattern.finditer(text))


def convert_ph_to_bptept(text: str) -> str:
    """`ph` 内の mq:rxt 表現で開始/終了タグに相当するものを `bpt`/`ept` に置換する。"""
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

    stack: list[tuple[str, str]] = []  # (disp, full_ph_text)
    replacements: list[tuple[str, str]] = []
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
        full_ph = m.group(0)
        tagname = _disp_to_tagname(disp)
        is_close = tagname.startswith('/')

        # 基本タグ名を抽出しておく（属性つき 'a href=...' 等を正規化）
        name_base = _base_tag(disp)

        # p は通常通りスタックでペア化を試みるが、
        # マッチする閉じタグがセグメント内に存在しない場合は it に変換する。

        if not is_close:
            # opening tag -> push
            stack.append((disp, full_ph))
        else:
            # closing tag -> try match with stack top
            if stack:
                open_disp, open_ph = stack[-1]
                open_name_base = _base_tag(open_disp)
                name_base = _base_tag(disp)
                if open_name_base == name_base:
                    stack.pop()
                    # build bpt/ept using the original disp values
                    open_inner = _mq_rxt_inner(open_disp, mode='open')
                    close_inner = _mq_rxt_inner(disp, mode='close')
                    i_val = pair_count
                    bpt = f"<bpt i='{i_val}'>{open_inner}</bpt>"
                    ept = f"<ept i='{i_val}'>{close_inner}</ept>"
                    replacements.append((open_ph, bpt))
                    replacements.append((full_ph, ept))
                    pair_count += 1
                else:
                    # 不整合なら、p タグであれば it pos='end' に変換
                    if name_base == 'p':
                        it_inner = _mq_rxt_inner(disp, mode='close')
                        it_tag = f"<it pos='end'>{it_inner}</it>"
                        replacements.append((full_ph, it_tag))
                    # それ以外は無視
                    continue
            else:
                # スタック空 -> 閉じタグが未対応。p なら it pos='end' にする
                if name_base == 'p':
                    it_inner = _mq_rxt_inner(disp, mode='close')
                    it_tag = f"<it pos='end'>{it_inner}</it>"
                    replacements.append((full_ph, it_tag))
                continue

    # スタックに残った開始タグで未ペアのものは処理する
    for open_disp, open_ph in stack:
        open_name_base = _base_tag(open_disp)
        if open_name_base == 'p':
            it_inner = _mq_rxt_inner(open_disp, mode='open')
            it_tag = f"<it pos='begin'>{it_inner}</it>"
            replacements.append((open_ph, it_tag))

    # apply replacements; replace longer old strings first to avoid partial overlap
    replacements_sorted = sorted(replacements, key=lambda x: -len(x[0]))
    for old, new in replacements_sorted:
        text = text.replace(old, new)

    return text

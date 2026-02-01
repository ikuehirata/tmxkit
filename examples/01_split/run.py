"""`input.tmx` を読み取り、`<prop type="x-document">` の値ごとに TMX を分割保存する。

使い方::

    python run.py

スクリプトは同ディレクトリの `input.tmx` を読み、分割結果を
`split/` ディレクトリに `.tmx` ファイルとして出力する。
"""

from __future__ import annotations

import re
from pathlib import Path

from tmxkit.io import stream_tu
from tmxkit.io.splitter_sink import consume_and_split


def _classify_by_x_document(tu) -> str | None:
    """`<prop type="x-document">` の値を取得し、拡張子を除いた文字列を分類キーとして返す。

    見つからない場合は `None` を返し、その TU は分割対象から除外される。
    """
    prop = tu.find('prop[@type="x-document"]')
    if prop is None:
        return None
    filename = (prop.text or '').strip()
    return re.sub(r'\.[^.]+$', '', filename)


def main() -> None:
    """エントリポイント。

    このファイルと同じディレクトリにある `input.tmx` を読み、
    `<prop type="x-document">` の値ごとに分割して `split/` 配下に出力する。
    """
    base = Path(__file__).parent
    input_path = base / 'input.tmx'
    out_dir = base / 'split'

    tu_stream = stream_tu(input_path)

    written = consume_and_split(
        input_stream=tu_stream,
        key_extractor=_classify_by_x_document,
        header_path=input_path,
        base_dir=out_dir,
    )
    print(written)

    total = sum(written.values())
    print(f'saved TUs: {total}')


if __name__ == '__main__':
    main()


"""
Merge two TMX files (`input1.tmx`, `input2.tmx`) into `output.tmx`.

実行すると同ディレクトリの `input1.tmx` と `input2.tmx` を逐次読み、
TU を結合して `output.tmx` として出力する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from tmxkit.io import merge_streams, stream_tu, write_tu_stream


def main() -> None:
    """エントリポイント。"""
    base = Path(__file__).parent
    inputs = [base / 'input1.tmx', base / 'input2.tmx']
    output = base / 'output.tmx'

    # 入力ストリームを作成
    streams: Iterable = (stream_tu(p) for p in inputs)

    # マージして書き出す
    merged = merge_streams(*streams)

    # ヘッダは先頭ファイルを参照する（None の場合はデフォルトヘッダ）
    written = write_tu_stream(
        tu_stream=merged,
        header_path=inputs[0],
        out_path=output,
    )

    print(f'saved TUs: {written}')


if __name__ == '__main__':
    main()


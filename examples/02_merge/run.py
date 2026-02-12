"""
Merge two TMX files (`input1.tmx`, `input2.tmx`) into `output.tmx`.

This script reads `input1.tmx` and `input2.tmx` sequentially, merges their
TUs, and writes the result to `output.tmx` in the same directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from tmxkit.core.models import TMXHeader
from tmxkit.io import merge_streams, stream_tu, write_tu_stream


def main() -> None:
    """Entry point."""
    base = Path(__file__).parent
    inputs = [base / 'input1.tmx', base / 'input2.tmx']
    output = base / 'output.tmx'

    # 入力ストリームを作成
    header = TMXHeader.from_tmx_file(inputs[0])
    streams: Iterable = (stream_tu(p) for p in inputs)

    # マージして書き出す
    merged = merge_streams(*streams)

    # ヘッダは先頭ファイルを参照する（None の場合はデフォルトヘッダ）
    written = write_tu_stream(
        tu_stream=merged,
        header_obj=header,
        out_path=output,
    )

    print(f'saved TUs: {written}')


if __name__ == '__main__':
    main()


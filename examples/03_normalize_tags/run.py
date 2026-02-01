"""テストランナー: `stream_tu` -> `pipeline.apply` -> `write_tu_stream` の流れで

`tmxkit.tu.tags.replace_tags` を適用して出力する。

使い方:
    python run.py input.tmx output.tmx

注: `tmxkit.io.writer.write_from_root` を使うと同等処理をまとめて実行できる。
"""
from __future__ import annotations

from pathlib import Path

from tmxkit.io import stream_tu, write_tu_stream
from tmxkit.pipeline.apply import apply
from tmxkit.tu.tags import replace_tags


def main() -> int:
    """実行エントリポイント。

    Parameters
    ----------
    argv : list[str] | None
        CLI 引数。None の場合 `sys.argv` を使用する。

    Returns
    -------
    int
        終了コード。
    """
    base = Path(__file__).parent
    input_path = base / 'input.tmx'
    output_path = base / 'output.tmx'

    # 1) stream_tu で TU ストリームを作成
    tu_stream = stream_tu(input_path)

    # 2) pipeline.apply を使って replace_tags を適用
    processed_stream = apply(tu_stream, replace_tags)

    # 3) write_tu_stream を使って出力（write_from_root を使っても良い）
    count = write_tu_stream(
        tu_stream=processed_stream,
        header_path=input_path,
        out_path=output_path,
    )

    print(f'Wrote {count} TU to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

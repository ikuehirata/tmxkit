"""Test runner: applies `tmxkit.tu.tags.replace_tags` in the flow

`stream_tu` -> `pipeline.apply` -> `write_tu_stream`.

"""
from __future__ import annotations

from pathlib import Path

from tmxkit.core.models import TMXHeader
from tmxkit.io import stream_tu, write_tu_stream
from tmxkit.pipeline.apply import apply
from tmxkit.tu.prepare import run


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Parameters
    ----------
    argv : list[str] | None
        CLI arguments. If None, `sys.argv` is used.

    Returns
    -------
    int
        Exit code.
    """
    base = Path(__file__).parent
    input_path = base / 'input.tmx'
    output_path = base / 'output.tmx'

    # 1) stream_tu で TU ストリームを作成
    header = TMXHeader.from_tmx_file(input_path)
    tu_stream = stream_tu(input_path)

    # 2) pipeline.apply を使って prepare.run を適用
    processed_stream = apply(tu_stream, lambda tu: run(header, tu))

    # 3) write_tu_stream を使って出力（write_from_root を使っても良い）
    count = write_tu_stream(
        tu_stream=processed_stream,
        header_obj=header,
        out_path=output_path,
    )

    print(f'Wrote {count} TU to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

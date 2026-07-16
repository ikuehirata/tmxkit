"""Tag normalization: uses `tmxkit.ops.merge` with `processors`.

Applies ``tmxkit.tu.prepare.run`` to each TU and writes the result.

Usage::

    python run.py
"""
from __future__ import annotations

from pathlib import Path

from tmxkit.core.models import TMXHeader
from tmxkit.ops import merge
from tmxkit.tu.prepare import run


def main() -> int:
    """Entry point.

    Returns
    -------
    int
        Exit code.
    """
    base = Path(__file__).parent
    input_path = base / 'input.tmx'
    output_path = base / 'output.tmx'

    # processors に渡す関数は (tu) -> tu の形。
    # prepare.run は header を必要とするため、クロージャで包む。
    header = TMXHeader.from_tmx_file(input_path)
    count = merge(
        [input_path],
        output_path,
        processors=[lambda tu: run(header, tu)],
    )

    print(f'Wrote {count} TU to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

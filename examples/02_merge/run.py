"""
Merge two TMX files (`input1.tmx`, `input2.tmx`) into `output.tmx`.

This script reads `input1.tmx` and `input2.tmx` sequentially, merges their
TUs, and writes the result to `output.tmx` in the same directory.
"""

from __future__ import annotations

from pathlib import Path

from tmxkit.ops import merge


def main() -> None:
    """Entry point."""
    base = Path(__file__).parent
    inputs = [base / 'input1.tmx', base / 'input2.tmx']
    output = base / 'output.tmx'

    written = merge(inputs, output)

    print(f'saved TUs: {written}')


if __name__ == '__main__':
    main()


"""Example: converting TMX to CSV

Uses tmxkit.ops.to_csv to convert a TMX file to CSV.

Usage:
    python run.py
"""

from pathlib import Path

from tmxkit.ops import to_csv


def main() -> None:
    """Entry point."""
    base = Path(__file__).parent
    input_file = base / 'input.tmx'
    output_file = base / 'output.csv'

    if input_file.exists():
        count = to_csv(input_file, output_file)
        print('✅ Converted to CSV: ' + str(output_file))
        print(f'   TUs processed: {count}')
    else:
        print('❌ Input file not found: ' + str(input_file))


if __name__ == '__main__':
    main()

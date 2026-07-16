"""Module providing a high-level API for exporting TMX to other formats.

Currently supported formats:
- CSV: `to_csv()`
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable

import lxml.etree as etree

from tmxkit.io import stream_tu
from tmxkit.tu.segment import get_text

Processor = Callable[[etree.Element], bool | None]


def to_csv(
    input_tmx: str | Path,
    output_csv: str | Path,
    filter_fn: Processor | None = None,
) -> int:
    """Stream-read a TMX file and convert it to CSV.

    Converts each TU's attributes, prop elements, and per-language segments
    (tuv) into CSV rows. Because it uses streaming processing, this is
    memory-efficient even for large TMX files.

    Parameters
    ----------
    input_tmx : str | Path
        Input TMX file path.
    output_csv : str | Path
        Output CSV file path.
    filter_fn : Processor | None, optional
        TU filtering function (returning False or None excludes the TU).
        Default is None (no filtering).

    Returns
    -------
    int
        Total number of TUs processed (output).

    Examples
    --------
    >>> from tmxkit.ops import to_csv
    >>> count = to_csv('input.tmx', 'output.csv')
    >>> print(f'Converted {count} TUs to CSV')

    Example with a filter:

    >>> def filter_by_client(tu):
    ...     prop = tu.find('prop[@type="client"]')
    ...     return prop is not None and prop.text == 'Electronic Arts'
    >>>
    >>> count = to_csv('input.tmx', 'output_ea.csv', filter_fn=filter_by_client)
    """
    input_tmx = Path(input_tmx)
    output_csv = Path(output_csv)

    _FIXED_FIELDS = ('changedate', 'creationdate', 'creationid', 'changeid')

    def _extract_row(tu_elem: etree.Element) -> dict:
        row: dict = {k: tu_elem.get(k) for k in _FIXED_FIELDS}
        for prop in tu_elem.findall('prop'):
            prop_type = prop.get('type')
            if prop_type:
                row[f'prop_{prop_type}'] = prop.text or ''
        for tuv in tu_elem.findall('tuv'):
            lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
            seg = tuv.find('seg')
            row[f'text_{lang}'] = get_text(seg) if seg is not None else ''
        return row

    # 1パス目: 全フィールド名を収集
    all_fields: set[str] = set()
    for tu_elem in stream_tu(input_tmx):
        if filter_fn is not None and not filter_fn(tu_elem):
            continue
        all_fields.update(_extract_row(tu_elem).keys())

    fieldnames = sorted(all_fields)

    # 2パス目: 書き込み
    tu_count = 0
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='')
        writer.writeheader()
        for tu_elem in stream_tu(input_tmx):
            if filter_fn is not None and not filter_fn(tu_elem):
                continue
            writer.writerow(_extract_row(tu_elem))
            tu_count += 1

    return tu_count

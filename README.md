# tmxkit

tmxkit is a Python library for safely handling very large TMX (Translation Memory eXchange) files in real-world workflows.

The library is designed around treating TMX not as a monolithic XML document but as a stream of `<tu>` (Translation Unit) elements.

tmxkit does not perform translation or proofreading. It provides the foundational utilities for working with translation data reliably and safely.

## Goals

- Process TMX files without expanding the entire document into memory.
- Decompose and reassemble `<tu>` elements as the minimal unit of work.
- Ensure rejoinability so human edits or external tools never break reassembly.
- Provide a pure library (no CLI or application-specific logic).

This library is not a translation tool — it's a lower-level building block for safely manipulating TMX files.

## Supported Format

- Supported: TMX (primarily version 1.4 series)
- Not supported:
  - Reproducing CAT-tool-specific behaviors
  - Full implementation of the entire TMX specification
  - Editing UIs or CLIs

tmxkit favors practical robustness over exhaustive specification conformance.

## Design Principles

- The library is stateless.
- Configuration, logging, and CLI concerns belong to higher-level layers.
- Avoid treating TMX as a huge in-memory XML tree.
- All processing is performed per-`<tu>`.

tmxkit aims to be quiet, fast, and unobtrusive — a foundation library.

## Project Layout

```
tmxkit/
├─ io/        # streaming TMX read/write/merge
├─ tu/        # utilities for <tu>, <prop>, <seg>
├─ pipeline/  # thin helpers to apply processing to TU streams
└─ errors.py
```

## Intended Usage

tmxkit centers on the model of "receive a TU, return a TU". Callers provide the processing logic.

Example:

```python
from pathlib import Path
from tmxkit.io.reader import stream_tu, read_header_only
from tmxkit.io.writer import write_tu_stream
from tmxkit.pipeline.apply import apply
from tmxkit.tu.props import replace_prop_value

def process_tu(tu: etree.Element) -> etree.Element:
  return replace_prop_value(tu, 'domain', 'ingame')

# Stream TUs from a single input file
tu_stream = stream_tu(input_path)
tu_stream = apply(tu_stream, process_tu)

write_tu_stream(
  tu_stream=tu_stream,
  header_path=Path(input_path),
  out_path=Path(output_path),
)
```

The example is illustrative of the design principle and not a complete runnable script.

## What This Library Does Not Do

- Translation or proofreading
- Manage configuration files
- Provide a CLI
- Act as a TMX editor

Those responsibilities should be handled by higher-level projects.

## Intended Consumers

- Preprocessing scripts for translation memories
- Custom tools that convert TMX into other formats

tmxkit's role is to safely stream TMX data without imposing processing decisions.

## Sources of Original Texts in `examples/`

The original text files included in the `examples/` directory are derived from **public-domain sources** listed below.
They are provided solely as sample data for demonstrating and testing the functionality of **tmxkit**.

### Sherlock Holmes (A Scandal in Bohemia)

* **English original text**  
  Project Gutenberg  
  *The Adventures of Sherlock Holmes*  
  “A Scandal in Bohemia”  
  [https://www.gutenberg.org/files/1661/1661-h/1661-h.htm#chap01](https://www.gutenberg.org/files/1661/1661-h/1661-h.htm#chap01)

* **Japanese translation**  
  Aozora Bunko  
  “ボヘミアの醜聞”  
  [https://www.aozora.gr.jp/cards/000009/files/226_31222.html](https://www.aozora.gr.jp/cards/000009/files/226_31222.html)

### The Pillow Book

* **English translation**  
  *The Pillow-Book of Sei Shōnagon*  
  translated by Arthur Waley (1928)  
  Internet Archive  
  [https://archive.org/stream/the-pillow-book/The%20Pillow%20Book_djvu.txt](https://archive.org/stream/the-pillow-book/The%20Pillow%20Book_djvu.txt)

* **Japanese original text**  
  Japanese Wikisource  
  *The Pillow Book (Makura no Sōshi)*, Section 1  
  [https://ja.wikisource.org/wiki/%E6%9E%95%E8%8D%89%E5%AD%90_(Wikisource)/%E7%AC%AC%E4%B8%80%E6%AE%B5](https://ja.wikisource.org/wiki/%E6%9E%95%E8%8D%89%E5%AD%90_%28Wikisource%29/%E7%AC%AC%E4%B8%80%E6%AE%B5)

All texts listed above are believed to be in the public domain.
They are included for demonstration purposes only, and no claim is made regarding translation accuracy or one-to-one alignment.

## Notes

This library is designed for practical, production use. It prioritizes:

- Not breaking input files
- Predictability
- Rejoinability

## License

MIT License

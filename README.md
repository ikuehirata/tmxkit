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
  header_root=read_header_only(Path(input_path)),
  final_path=Path(output_path),
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

## Notes

This library is designed for practical, production use. It prioritizes:

- Not breaking input files
- Predictability
- Rejoinability

## License

MIT License

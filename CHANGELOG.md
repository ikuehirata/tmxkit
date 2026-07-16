# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-07-16

### Added
- Added a `strict` option to `ops.merge` (raises `ValueError` on TU count mismatch)
- Added `ops.to_csv` (streams a TMX and converts it to CSV)
- Added `stream_tu_fragment` (a streaming read API for TU fragment files with no root element)
- Created dataclasses for TU
- Made the `apply` function more resilient to errors — when an error occurs, the affected TU can be recovered via `on_error`
- Added new-file initialization handling to `TMXWriter`, plus a backup feature

### Changed
- Unified logging on the standard `logging` module
- Added `from __future__ import annotations` to all modules
- Changed `TMXWriter.flush` from a read-whole-file-and-rewrite approach to an append-based one, eliminating the O(n²) write cost of rereading the entire output on every flush
- Clarified the append semantics of `ops.merge` against an existing `output`, and changed `strict`'s TU count validation to check the total TU count of the output file
- Reused the previously unused `_remove_tmx_footer` inside the append-mode implementation, removing the duplicate definition of the footer byte string
- Cleaned up unreachable code at the top of `tu/split.py`

### Removed
- Removed `stream_tu`'s implicit TU-only fallback reading (fragment file reading is now split out into `stream_tu_fragment`)

### Fixed
- Made writing possible when reusing a file during TMX split
- Prevented tag nesting
- Fixed a bug where specifying `header_path`/`header_obj` in `write_tu_stream` / `TMXWriter` still had the output header replaced with the default, losing `srclang` and other fields
- Fixed a bug where closing an existing file with no appends in `TMXWriter.finalize` produced a doubled footer (`</body></tmx>` written twice)
- Fixed a bug where `TMXWriter.count` also counted TUs saved to the error file as written (split out `error_count` as a separate public property)
- Fixed a bug where, with a shared `error_path`, a later `TMXWriter` initialization would overwrite and erase TUs saved by an earlier writer
- Fixed a bug where `stream_tu` returned empty text when a `<seg>`'s first content was a child element (e.g. `<seg><ph>x</ph>hello</seg>`)
- Fixed a bug where retaining a TU returned by `stream_tu(parse=True)` would leave `raw_xml` and tag information empty due to internal `clear()` calls (now `deepcopy`d before being retained)
- Added root element validation to `stream_tu` to fix an issue where passing a fragment file silently returned partial results
- Fixed a bug in `convert_ph_to_bptept` where the `i` numbers of `bpt`/`ept` were all the same when multiple pairs of the same tag existed (changed to position-based replacement)
- Fixed a bug in `prepare.run` / `get_segment` where segments were left unprocessed and skipped if `xml:lang` casing didn't match exactly (e.g. `EN` vs `en`)
- Fixed a bug where `ops.to_csv` would stop with a `ValueError` if a prop / language column absent from the first TU appeared in a later TU (changed to collect column names in two passes)
- Fixed `TMXHeader.creationtoolversion` to lazily resolve the version at instance creation instead of at class definition time (avoids import failures in environments where the package isn't installed)
- Fixed the behavior where `TMXHeader.from_tmx_file` implicitly fell back to `'ja'` when `targetlang` was unset; it now stays `None` and emits a warning instead
- Fixed a bug in `TU.get()` where an empty-string attribute value was still replaced with the `default` value
- Fixed a potential issue in `segment.get_text` where `tostring`'s tail text could leak in (now explicitly passes `with_tail=False`)
- Fixed a bug where no file was created when writing out an empty TU stream
- Used UUIDs in `tags.py` placeholders, removing the risk of collisions between the original text and placeholder strings
- Fixed references to nonexistent APIs (`write_from_roots`, `read_header_only`, etc.) that remained in documentation and warning messages

## [0.2.0] - 2026-02-12

### Added
- Created `split` for splitting TUs. Currently supports splitting only on `<ph type="fmt">{}</ph>` (equivalent to memoQ's x tags). The delimiter itself is removed
- Added `prepare.py`, an orchestration module for TU cleanup
- Created a TMX header dataclass in `core/models.py`. Its main purpose is reading the source and target languages from the header. Handling for when the target language is absent from the header is not yet implemented
- Added `tu/normalize.py`, enabling whitespace normalization

### Fixed
- Changed `tu/segment.py` to thoroughly target only `<seg>`
- Added space normalization to tag fixes (to be split out later)
- Fixed an issue where the output directory structure was duplicated when splitting a TMX

## [0.1.1] - 2026-02-02

### Added
- Added tag normalization functionality
- Added samples for TMX split, tag fixing, and TMX merge

### Fixed
- Renamed `io/splitter.py` to `io/splitter_sink.py`, clarifying the separation of responsibilities from `io/writer.py`

## [0.1.0] - 2026-01-11

### Added
- Initial release of tmxkit

[Unreleased]: https://github.com/ikuehirata/tmxkit/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/ikuehirata/tmxkit/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/ikuehirata/tmxkit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/ikuehirata/tmxkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ikuehirata/tmxkit/releases/tag/v0.1.0

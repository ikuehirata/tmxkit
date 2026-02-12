# Changelog

## [0.2.0]

### Fixed
### Fixed
- Changed `tu/segment.py` to operate strictly on `<seg>` elements only.
- Added space normalization to tag fixes (will be extracted/separated later).
- Fixed phenomenon where output directory structure will be double by splitting a TMX.

### Added
### Added
- Added `split` utility to split TUs. Currently it supports splitting only on
	`<ph type="fmt">{}</ph>` markers (equivalent to memoQ's x-tag). The marker
	itself is removed from the results.
- Added orchestration `prepare.py` for TU cleanup.
- Added a dataclass for the TMX header in `core/models.py`.
	The primary purpose is to read source and target languages from the header.
	Handling for cases where the target language is not present in the header is
	not yet implemented.
- Added `tu/normalize.py` to normalize whitespace.

## [0.1.1]

### Fixed
- Removed `io/splitter.py` and renamed it to `io/splitter_sink.py` to clarify separation of responsibilities from `io/writer.py`.

### Added
- Added tag normalization function.
- Examples for TMX splitting, tag fixing, TMX merging.

## [0.1.0]

### Added
- Initial release of tmxkit.

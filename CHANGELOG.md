# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Research polling CLI commands** for LLM agent workflows:
  - `notebooklm research status` - Check research progress (non-blocking)
  - `notebooklm research wait --import-all` - Wait for completion and import sources
  - `notebooklm source add-research --no-wait` - Start deep research without blocking
  - Enables subagent pattern for long-running deep research operations

### Enhanced
- **Multi-artifact downloads**: All download commands now support advanced multi-artifact features:
  - `download audio` - Download all audio overviews with intelligent selection
  - `download video` - Download all video overviews with intelligent selection
  - `download infographic` - Download all infographics with intelligent selection
  - `download slide-deck` - Download all slide decks with directory-based organization

  Each command now includes:
  - Multiple artifact selection (--all flag)
  - Smart defaults (optional OUTPUT_PATH)
  - Intelligent filtering (--latest, --earliest, --name, --artifact-id)
  - File/directory conflict handling (--force, --no-clobber, auto-rename)
  - Preview mode (--dry-run)
  - Structured output (--json)
  - Safe filename generation from artifact titles
  - Progress indicators for batch downloads
  - Detailed result reporting (downloaded/skipped/failed)

### Added
- `select_artifact()` helper for intelligent artifact selection
- `artifact_title_to_filename()` helper for safe filename conversion
- `_download_artifacts_generic()` - Generic download implementation for all artifact types
- `_display_download_result()` - Unified result display helper

### Refactored
- Eliminated 677 lines of duplicated download code (21.4% reduction):
  - Before: 4 commands × ~320 lines = ~1,280 lines of duplicated logic
  - After: 1 generic function (~300 lines) + 4 thin wrappers (~65 lines each)
  - Result: Improved maintainability and consistency across all download commands

## [0.1.0] - 2026-01-05

### Added
- Initial release of `notebooklm-py` - unofficial Python client for Google NotebookLM
- Full notebook CRUD operations (create, list, rename, delete)
- Source management:
  - Add URL sources (with YouTube transcript support)
  - Add text sources
  - Add file sources (PDF, TXT, MD, DOCX) via native upload
  - Delete sources
  - Rename sources
- Studio artifact generation:
  - Audio overviews (podcasts) with 4 formats and 3 lengths
  - Video overviews with 9 visual styles
  - Quizzes and flashcards
  - Infographics, slide decks, and data tables
  - Study guides, briefing docs, and reports
- Query/chat interface with conversation history support
- Research agents (Fast and Deep modes)
- Artifact downloads (audio, video, infographics, slides)
- CLI with 27 commands
- Comprehensive documentation (API, RPC, examples)
- 96 unit tests (100% passing)
- E2E tests for all major features

### Fixed
- Audio overview instructions parameter now properly supported at RPC position [6][1][0]
- Quiz and flashcard distinction via title-based filtering
- Package renamed from `notebooklm-automation` to `notebooklm`
- CLI module renamed from `cli.py` to `notebooklm_cli.py`
- Removed orphaned `cli_query.py` file

### API Changes
- Renamed collection methods to use `list_*` pattern (e.g., `get_quizzes()` → `list_quizzes()`)
- Split `get_notes()` into `list_notes()` and `list_mind_maps()`
- Added `get_artifact(notebook_id, artifact_id)` for single-item retrieval
- Old methods kept as deprecated wrappers with warnings

### ⚠️ Beta Release Notice

This is the initial public release of `notebooklm-py`. While core functionality is tested and working, please note:

- **RPC Protocol Fragility**: This library uses reverse-engineered Google APIs. Method IDs can change without notice, potentially breaking functionality. See [Troubleshooting](docs/troubleshooting.md) for debugging guidance.
- **Unofficial Status**: This is not affiliated with or endorsed by Google.
- **API Stability**: The Python API may change in future releases as we refine the interface.

### Known Issues

- **RPC method IDs may change**: Google can update their internal APIs at any time, breaking this library. Check the [RPC Protocol](docs/contributing/rpc-protocol.md) guide for how to identify and update method IDs.
- **Rate limiting**: Heavy usage may trigger Google's rate limits. Add delays between bulk operations.
- **Quiz/flashcard generation**: May return `None` in some cases (requires further RPC investigation).
- **Authentication expiry**: CSRF tokens expire after some time. Re-run `notebooklm login` if you encounter auth errors.
- **Large file uploads**: Files over 50MB may fail or timeout. Split large documents if needed.

[0.1.0]: https://github.com/teng-lin/notebooklm-py/releases/tag/v0.1.0

# Smart Download CLI Design

**Date:** 2026-01-07
**Status:** Approved (revised after Gemini critique)
**Author:** Claude Code (brainstorming session)

## Overview

Redesign the `notebooklm download` command to auto-detect artifact types, support batch downloads, and provide a better user experience.

## Current State

```bash
# Current: requires explicit type
notebooklm download audio ./output.mp3
notebooklm download video ./output.mp4
notebooklm download slides ./output.pdf
notebooklm download infographic ./output.png
```

**Problems:**
- User must know artifact type
- User must specify output filename
- No batch download support
- No way to download all artifacts at once

## Proposed Design

### Command Syntax

```bash
# Smart single download (auto-detect type)
notebooklm download <artifact_id>

# Smart single with custom output
notebooklm download <artifact_id> -o <path>

# Batch download
notebooklm download <id1> <id2> <id3>

# Download all artifacts
notebooklm download --all

# Download all with type filter
notebooklm download --all --type audio
notebooklm download --all --type video,slides

# With output directory
notebooklm download --all -o ./downloads

# Preview mode
notebooklm download --all --dry-run

# Force overwrite existing files
notebooklm download --all --overwrite
```

### Artifact Discovery

Users find artifact IDs using existing commands:

```bash
# List all artifacts with IDs
notebooklm artifact list

# Example output:
# abc123  Research Overview    audio   completed   2026-01-07
# def456  Deep Dive           video   completed   2026-01-07
# ghi789  Chapter Quiz        quiz    completed   2026-01-07
```

### Auto-Detection Logic

The system looks up the artifact by ID and determines:
1. Artifact type (audio, video, slides, infographic, quiz, etc.)
2. Whether it's downloadable
3. Appropriate file extension

```
Artifact ID → Lookup → Type Detection → Download or Error
```

### Downloadable vs Non-Downloadable

| Type | Downloadable | Extension | Notes |
|------|--------------|-----------|-------|
| Audio (podcast) | Yes | .mp3 | |
| Video | Yes | .mp4 | |
| Slides | Yes | .pdf | |
| Infographic | Yes | .png | |
| Quiz | No | - | View in NotebookLM UI |
| Flashcards | No | - | View in NotebookLM UI |
| Mind Map | No | - | View in NotebookLM UI |
| Data Table | No | - | Export to Google Sheets |
| Report | No | - | Export to Google Docs |

### Filename Generation

**Default behavior:** Use artifact title, sanitized for filesystem safety.

```python
def sanitize_filename(title: str) -> str:
    """Convert artifact title to safe filename.

    Rules:
    1. Remove unsafe characters: < > : " / \\ | ? *
    2. Replace spaces with underscores
    3. Collapse multiple underscores to single
    4. Strip leading/trailing underscores
    5. Truncate to 100 characters (before extension)
    6. Fallback to "Untitled_{type}_{id[:8]}" if empty
    """
    if not title or not title.strip():
        return None  # Caller handles fallback

    # Remove unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    # Collapse multiple underscores
    safe = re.sub(r'_+', '_', safe)
    # Strip leading/trailing
    safe = safe.strip('_')
    # Truncate
    return safe[:100] if safe else None
```

**Examples:**
- `"Research Overview"` → `Research_Overview.mp3`
- `"Deep Dive: AI Ethics"` → `Deep_Dive_AI_Ethics.mp4`
- `"My Report (Draft)"` → `My_Report_Draft.pdf`
- `"Research: Q1/Q2 (2025)"` → `Research_Q1_Q2_2025.mp3`
- `""` or `"   "` → `Untitled_audio_abc123.mp3`

### Filename Collision Handling

When multiple artifacts would produce the same filename:

```bash
# Two audio files titled "Weekly Summary"
Weekly_Summary.mp3      # First one
Weekly_Summary_2.mp3    # Second one (counter suffix)
Weekly_Summary_3.mp3    # Third one
```

Implementation:
```python
def get_unique_filename(base_path: Path) -> Path:
    """Add counter suffix if file exists."""
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 2

    while True:
        new_path = base_path.parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
```

### Output Behavior

| Command | Output Location |
|---------|-----------------|
| `download <id>` | Current directory, title-based name |
| `download <id> -o file.mp3` | Specified file path |
| `download <id> -o ./dir/` | Specified directory, title-based name |
| `download id1 id2` | Current directory, title-based names |
| `download --all` | Current directory, title-based names |
| `download --all -o ./dir` | Specified directory, title-based names |

### Notebook Context

Downloads use the active notebook from `notebooklm use`:

```bash
notebooklm use abc123      # Set active notebook
notebooklm download --all  # Downloads from abc123
```

Override with explicit flag:
```bash
notebooklm download --all --notebook def456
```

Error if no context:
```bash
$ notebooklm download --all
Error: No notebook selected. Run 'notebooklm use <id>' or specify --notebook.
Exit code: 2
```

### Conflict Handling

When a file already exists:

**Default:** Skip with warning
```
⚠ Skipped: Research_Overview.mp3 (already exists, use --overwrite)
```

**With `--overwrite`:** Replace existing files
```
✓ Overwrote: Research_Overview.mp3
```

### Error Handling

#### Single Download - Non-Downloadable

```bash
$ notebooklm download abc123  # abc123 is a quiz
✗ Cannot download: "Chapter Quiz" is a Quiz
  Quizzes are not downloadable. View in NotebookLM UI instead.
Exit code: 1
```

#### Single Download - Not Found

```bash
$ notebooklm download xyz789
✗ Artifact not found: xyz789
Exit code: 1
```

#### Batch Download - Mixed Results

```bash
$ notebooklm download id1 id2 id3  # id2 is flashcards
✓ Downloaded: Research_Overview.mp3
⚠ Skipped: Study Cards (flashcards - not downloadable)
✓ Downloaded: Summary.pdf

Downloaded: 2 | Skipped: 1 non-downloadable
Exit code: 0
```

#### Batch Download - Partial Failures

```bash
$ notebooklm download id1 id2 id3  # id2 has network error
✓ Downloaded: Research_Overview.mp3
✗ Failed: Deep_Dive.mp4 (network timeout)
✓ Downloaded: Summary.pdf

Downloaded: 2 | Failed: 1
Exit code: 1
```

#### Download All - Mixed Results

```bash
$ notebooklm download --all
✓ Downloaded: Research_Overview.mp3
✓ Downloaded: Deep_Dive.mp4
⚠ Skipped: Chapter Quiz (quiz - not downloadable)
⚠ Skipped: Study Cards (flashcards - not downloadable)
⚠ Skipped: Concept Map (mind-map - not downloadable)
✓ Downloaded: Summary.pdf

Downloaded: 3 | Skipped: 3 non-downloadable
Exit code: 0
```

#### No Artifacts

```bash
$ notebooklm download --all
No downloadable artifacts found in notebook.
Exit code: 0
```

### Dry Run Mode

Preview what would be downloaded without actually downloading:

```bash
$ notebooklm download --all --dry-run
Would download:
  ✓ abc123: "Research Overview" (audio) → Research_Overview.mp3
  ✓ def456: "Deep Dive" (video) → Deep_Dive.mp4
  ✓ jkl012: "Summary" (slides) → Summary.pdf

Not downloadable:
  ✗ ghi789: "Chapter Quiz" (quiz)
  ✗ mno345: "Study Cards" (flashcards)
  ✗ pqr678: "Concept Map" (mind-map)

Would download: 3 files
```

With conflicts:
```bash
$ notebooklm download --all --dry-run
Would download:
  ✓ abc123: "Research Overview" (audio) → Research_Overview.mp3
  ⚠ def456: "Deep Dive" (video) → Deep_Dive.mp4 (exists, use --overwrite)

Would download: 1 file | Would skip: 1 existing
```

### Type Filtering

Filter `--all` by artifact type:

```bash
# Download only audio files
notebooklm download --all --type audio

# Download audio and video
notebooklm download --all --type audio,video

# Available types: audio, video, slides, infographic
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All requested downloadable artifacts succeeded (skipping non-downloadable is OK) |
| 1 | At least one downloadable artifact failed (network error, not found, etc.) |
| 2 | Invalid usage (no notebook context, bad arguments) |

**Rationale:** Exit 0 means "nothing went wrong with what we tried to download." Skipping non-downloadable types is expected behavior, not an error.

### JSON Output

All commands support `--json` for machine-readable output:

```bash
$ notebooklm download --all --json
```

```json
{
  "downloaded": [
    {"id": "abc123", "title": "Research Overview", "type": "audio", "path": "Research_Overview.mp3"},
    {"id": "def456", "title": "Deep Dive", "type": "video", "path": "Deep_Dive.mp4"}
  ],
  "skipped": [
    {"id": "ghi789", "title": "Chapter Quiz", "type": "quiz", "reason": "not_downloadable"},
    {"id": "jkl012", "title": "Old File", "type": "audio", "reason": "already_exists"}
  ],
  "failed": [
    {"id": "mno345", "title": "Broken", "type": "video", "error": "Network timeout"}
  ],
  "summary": {
    "downloaded": 2,
    "skipped": 2,
    "failed": 1
  }
}
```

## CLI Options Summary

```
notebooklm download [OPTIONS] [ARTIFACT_IDS]...

Arguments:
  ARTIFACT_IDS    One or more artifact IDs to download (optional if --all)

Options:
  --all             Download all downloadable artifacts in current notebook
  --type TYPE       Filter by type: audio, video, slides, infographic (comma-separated)
  -o, --output      Output path (file for single, directory for multiple)
  --overwrite       Overwrite existing files (default: skip)
  --dry-run         Preview without downloading
  -n, --notebook    Notebook ID (uses current context if not specified)
  --json            Output in JSON format
  --help            Show help message
```

## Backward Compatibility

The existing explicit commands remain available for users who prefer them:

```bash
# These still work
notebooklm download audio ./output.mp3
notebooklm download video ./output.mp4 -a <artifact_id>
```

The new smart download is additive, not a breaking change.

## Implementation Notes

### Artifact Type Detection

Use existing `artifact list` functionality to:
1. Fetch artifact by ID
2. Check `artifact_type` field
3. Map to downloadable status and extension

```python
DOWNLOADABLE_TYPES = {
    StudioContentType.AUDIO_OVERVIEW: (".mp3", "audio"),
    StudioContentType.VIDEO_OVERVIEW: (".mp4", "video"),
    StudioContentType.SLIDE_DECK: (".pdf", "slides"),
    StudioContentType.INFOGRAPHIC: (".png", "infographic"),
}

def is_downloadable(artifact: Artifact) -> bool:
    return artifact.artifact_type in DOWNLOADABLE_TYPES

def get_extension(artifact: Artifact) -> str:
    return DOWNLOADABLE_TYPES.get(artifact.artifact_type, (None, None))[0]

def get_type_name(artifact: Artifact) -> str:
    return DOWNLOADABLE_TYPES.get(artifact.artifact_type, (None, "unknown"))[1]
```

### Batch Download Implementation

```python
@dataclass
class DownloadResult:
    downloaded: list[DownloadedArtifact] = field(default_factory=list)
    skipped: list[SkippedArtifact] = field(default_factory=list)
    failed: list[FailedArtifact] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return len(self.failed) > 0

async def download_batch(
    artifact_ids: list[str],
    output_dir: Path,
    overwrite: bool = False,
    type_filter: set[str] | None = None,
) -> DownloadResult:
    results = DownloadResult()

    for artifact_id in artifact_ids:
        try:
            artifact = await client.artifacts.get(artifact_id)
        except ArtifactNotFoundError:
            results.failed.append(FailedArtifact(artifact_id, "not found"))
            continue

        # Check type filter
        type_name = get_type_name(artifact)
        if type_filter and type_name not in type_filter:
            results.skipped.append(SkippedArtifact(artifact, "filtered_out"))
            continue

        if not is_downloadable(artifact):
            results.skipped.append(SkippedArtifact(artifact, "not_downloadable"))
            continue

        # Generate filename
        filename = sanitize_filename(artifact.title)
        if not filename:
            filename = f"Untitled_{type_name}_{artifact.id[:8]}"
        filename += get_extension(artifact)

        output_path = get_unique_filename(output_dir / filename)

        if output_path.exists() and not overwrite:
            results.skipped.append(SkippedArtifact(artifact, "already_exists"))
            continue

        try:
            await download_artifact(artifact, output_path)
            results.downloaded.append(DownloadedArtifact(artifact, output_path))
        except Exception as e:
            results.failed.append(FailedArtifact(artifact, str(e)))

    return results
```

## Testing Plan

### Unit Tests
- Filename sanitization edge cases (special chars, unicode, empty, long)
- Filename collision counter logic
- Downloadable type detection
- Exit code logic
- Type filter parsing

### Integration Tests
- Mock artifact lookup and download
- JSON output format validation
- Batch processing with mixed results
- Partial failure handling

### E2E Tests
- Download single artifact
- Download multiple artifacts
- Download all with mixed types
- Download with type filter
- Dry run mode
- Conflict handling (skip vs overwrite)
- Filename collision resolution

## Future Considerations (P1)

These features are recommended for follow-up implementation:

### Progress Bars
Large video files (100+ MB) need progress indication:
```bash
Downloading Deep_Dive.mp4... ██████████░░░░ 60% (27.1/45.1 MB)
```
Use `rich` library. Add `--quiet` flag to disable.

### Concurrent Downloads
Sequential download of 50 artifacts is slow:
```bash
notebooklm download --all --concurrent 3  # Default: 3
```

### Rate Limit Handling
Google may rate-limit large batch downloads:
- Detect 429 errors
- Automatic exponential backoff
- Warning message to user

## Future Considerations (P2)

Nice-to-have features for later:

- **Resume support:** `--resume` to skip already-downloaded files
- **Metadata sidecars:** `--with-metadata` saves .json with artifact info
- **Output templates:** `--template '{type}_{date}_{title}'`
- **Archive bundle:** `--archive notebook.zip`
- **Interactive mode:** TUI picker for selecting artifacts

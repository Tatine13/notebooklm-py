# Testing Guide

**Status:** Active
**Last Updated:** 2026-01-08

## Prerequisites

Before running ANY E2E tests, you must complete this setup:

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### 2. Authenticate with NotebookLM

```bash
notebooklm login
```

This opens a browser, logs into your Google account, and stores cookies in `~/.notebooklm/storage.json`.

Verify with:
```bash
notebooklm status
```

### 3. Create Your Test Notebook (REQUIRED)

**You MUST create a personal test notebook** with content. Tests will exit with an error if not configured.

1. Go to [NotebookLM](https://notebooklm.google.com)
2. Create a new notebook (e.g., "E2E Test Notebook")
3. Add multiple sources:
   - At least one text/paste source
   - At least one URL source
   - Optionally: PDF, YouTube video
4. Generate some artifacts:
   - At least one audio overview
   - At least one quiz or flashcard set
5. Copy the notebook ID from the URL: `notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID`
6. Create your `.env` file:

```bash
cp .env.example .env
# Edit .env and set your notebook ID
```

Or set the environment variable directly:
```bash
export NOTEBOOKLM_TEST_NOTEBOOK_ID="your-notebook-id-here"
```

### 4. Verify Setup

```bash
# Should pass - unit tests don't need auth
pytest tests/unit/

# Should pass - uses your test notebook
pytest tests/e2e -m readonly -v
```

If tests skip with "no auth stored" or fail with permission errors, your setup is incomplete.

---

## Quick Reference

```bash
# Run unit + integration tests (default, no auth needed)
pytest

# Run E2E tests (requires setup above)
pytest tests/e2e -m readonly        # Read-only tests only (~2 min)
pytest tests/e2e -m "not slow"      # Skip generation tests (~5 min)
pytest tests/e2e -m "not variants"  # Skip variant tests (~30 min)
pytest tests/e2e -m variants        # Only variant tests
pytest tests/e2e                    # ALL tests (~2 hours, high quota)
```

## Test Structure

```
tests/
├── conftest.py              # RPC response builders
├── unit/                    # No network, fast
│   ├── cli/                 # CLI command tests
│   ├── test_decoder.py
│   ├── test_encoder.py
│   └── ...
├── integration/             # Mocked HTTP
│   ├── conftest.py          # Mock auth tokens
│   └── test_*.py
└── e2e/                     # Real API
    ├── conftest.py          # Auth, fixtures, cleanup
    ├── test_generation.py   # All artifact generation tests
    ├── test_artifacts.py    # Artifact CRUD/list operations
    ├── test_downloads.py    # Download operations
    ├── test_sources.py      # Source operations
    └── ...
```

## E2E Fixtures

### Which Fixture Do I Need?

| I want to... | Use | Why |
|--------------|-----|-----|
| List/download existing artifacts | `test_notebook_id` | Your notebook with pre-made content |
| Add/delete sources or notes | `temp_notebook` | Isolated, auto-cleanup |
| Generate audio/video/quiz | `generation_notebook` | Writable, has content, session-scoped |

### `test_notebook_id` (Your Test Notebook - REQUIRED)

Returns `NOTEBOOKLM_TEST_NOTEBOOK_ID` env var. **Tests will exit with an error if not set.**

Your notebook must have:
- Multiple sources (text, URL, etc.)
- Pre-generated artifacts (audio, quiz, etc.)

```python
@pytest.mark.readonly
async def test_list_artifacts(self, client, test_notebook_id):
    artifacts = await client.artifacts.list(test_notebook_id)
    assert isinstance(artifacts, list)
```

### `temp_notebook`

Fresh notebook per test. Automatically deleted after test completes (even on failure).

```python
async def test_add_source(self, client, temp_notebook):
    source = await client.sources.add_url(temp_notebook.id, "https://example.com")
    assert source.id is not None
```

### `generation_notebook`

Session-scoped notebook with content. Created once, shared across all generation tests.

```python
@pytest.mark.slow
async def test_generate_quiz(self, client, generation_notebook):
    result = await client.artifacts.generate_quiz(generation_notebook.id)
    assert result is not None
```

**Why not readonly?** You can't generate on notebooks you don't own.
**Why not temp_notebook?** Creating fresh notebooks per test wastes quota.
**Cleanup:** Automatic - the entire notebook is deleted at session end, removing all artifacts.

## Test Markers

All markers defined in `pyproject.toml`:

| Marker | Purpose |
|--------|---------|
| `slow` | Tests taking 30+ seconds (generation, polling) |
| `variants` | Parameter variant tests (skip to save quota) |
| `readonly` | Read-only tests against user's test notebook |

### Variant Testing

Each artifact type has multiple options. We test one default per type, mark variants with `@pytest.mark.variants`:

```python
# Runs by default
@pytest.mark.slow
async def test_generate_audio_default(self, client, generation_notebook):
    result = await client.artifacts.generate_audio(generation_notebook.id)

# Only when requested: pytest -m variants
@pytest.mark.slow
@pytest.mark.variants
async def test_generate_audio_brief(self, client, generation_notebook):
    result = await client.artifacts.generate_audio(
        generation_notebook.id,
        audio_format=AudioFormat.BRIEF,
    )
```

## E2E Fixtures Reference

From `tests/e2e/conftest.py`:

### Authentication

```python
@pytest.fixture(scope="session")
def auth_cookies() -> dict[str, str]:
    """Load cookies from ~/.notebooklm/storage.json"""

@pytest.fixture(scope="session")
def auth_tokens(auth_cookies) -> AuthTokens:
    """Fetch CSRF + session ID from NotebookLM homepage"""

@pytest.fixture
async def client(auth_tokens) -> NotebookLMClient:
    """Fresh client per test"""
```

### Notebooks

```python
@pytest.fixture
def test_notebook_id() -> str:
    """Returns NOTEBOOKLM_TEST_NOTEBOOK_ID (required)"""

@pytest.fixture
async def temp_notebook(client) -> Notebook:
    """Create notebook, auto-delete after test"""

@pytest.fixture(scope="session")
async def generation_notebook(auth_tokens) -> Notebook:
    """Session notebook with content for generation tests"""
```

### Decorators

```python
@requires_auth  # Skip test if no auth stored
```

## Environment Variables

Set via `.env` file (recommended) or shell export:

```bash
# Required: Your test notebook with sources and artifacts
NOTEBOOKLM_TEST_NOTEBOOK_ID=your-notebook-id-here
```

See `.env.example` for the template.

## Writing New Tests

### Decision Tree

```
Need network?
├── No → tests/unit/
├── Mocked → tests/integration/
└── Real API → tests/e2e/
    └── What notebook?
        ├── Read-only → test_notebook_id + @pytest.mark.readonly
        ├── CRUD → temp_notebook
        └── Generation → generation_notebook + @pytest.mark.slow
            └── Variant? → add @pytest.mark.variants
```

### Example: New Generation Test

Add generation tests to `tests/e2e/test_generation.py`:

```python
@requires_auth
class TestNewArtifact:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_new_artifact_default(self, client, generation_notebook):
        result = await client.artifacts.generate_new(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_new_artifact_with_options(self, client, generation_notebook):
        result = await client.artifacts.generate_new(
            generation_notebook.id,
            option=SomeOption.VALUE,
        )
        assert result is not None
```

Note: Generation tests only need `client` and `generation_notebook`. Cleanup is handled automatically when the session-scoped notebook is deleted at session end.

## Troubleshooting

### Tests skip with "no auth stored"

Run `notebooklm login` and complete browser authentication.

### Tests fail with permission errors

Your `NOTEBOOKLM_TEST_NOTEBOOK_ID` may be invalid or you don't own it. Verify:
```bash
echo $NOTEBOOKLM_TEST_NOTEBOOK_ID
notebooklm list  # Should show your notebooks
```

### Tests hang or timeout

- **Generation tests:** Can take 5-15 minutes for audio/video. This is normal.
- **Rate limiting:** NotebookLM has undocumented rate limits. Add delays between test runs.
- **CSRF token expired:** Run `notebooklm login` again.

### "CSRF token invalid" or 403 errors

Your session expired. Re-authenticate:
```bash
notebooklm login
```

### "NOTEBOOKLM_TEST_NOTEBOOK_ID not set" error

This is expected - E2E tests require your own notebook. Follow Prerequisites step 3 to create one.

### Too many artifacts accumulating

Generation tests create artifacts in `generation_notebook` (deleted at session end) and `temp_notebook` (deleted per test). If you interrupt tests, orphaned notebooks may remain. Clean up manually in the NotebookLM UI.

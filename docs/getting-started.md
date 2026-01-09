# Getting Started

**Status:** Active
**Last Updated:** 2026-01-08

This guide walks you through installing and using `notebooklm-py` for the first time.

## Prerequisites

- Python 3.9 or higher
- A Google account with access to [NotebookLM](https://notebooklm.google.com)

## Installation

### Basic Installation (CLI + Python API)

```bash
pip install notebooklm-py
```

### With Browser Login Support (Recommended for first-time setup)

```bash
pip install "notebooklm-py[browser]"
playwright install chromium
```

The browser extra installs Playwright, which is **only required for `notebooklm login`**. All other commands and the Python API use standard HTTP requests via `httpx`.

> **Headless/Remote Machines:** If you've already authenticated on another machine, copy `~/.notebooklm/storage_state.json` and use the basic installation without Playwright. See [Configuration - Headless Servers](configuration.md#headless-servers--containers).

### Development Installation

```bash
git clone https://github.com/teng-lin/notebooklm-py.git
cd notebooklm-py
pip install -e ".[all]"
playwright install chromium
```

> **See also:** [Configuration](configuration.md) for custom storage paths and environment settings.

## Authentication

NotebookLM uses Google's internal APIs, which require valid session cookies. The CLI provides a browser-based login flow:

```bash
notebooklm login
```

This will:
1. Open a Chromium browser window
2. Navigate to NotebookLM
3. Wait for you to log in with your Google account
4. Save your session to `~/.notebooklm/storage_state.json`

**Note:** The browser uses a persistent profile at `~/.notebooklm/browser_profile/` to avoid Google's bot detection. This makes it appear as a regular browser installation.

**Custom Locations:** Set `NOTEBOOKLM_HOME` to store all configuration files in a different directory:
```bash
export NOTEBOOKLM_HOME=/custom/path
notebooklm login
```

See [Configuration](configuration.md) for multiple accounts, CI/CD setup, and more options.

### Verifying Authentication

After login, verify your session works:

```bash
notebooklm list
```

This should show your existing notebooks (or an empty list if you're new to NotebookLM).

## Your First Workflow

Let's create a notebook, add a source, and generate a podcast.

### Step 1: Create a Notebook

```bash
notebooklm create "My First Notebook"
```

Output:
```
Created notebook: abc123def456
Title: My First Notebook
```

### Step 2: Set the Active Notebook

```bash
notebooklm use abc123def456
```

You can use partial IDs - `notebooklm use abc` will match `abc123def456`.

### Step 3: Add a Source

```bash
notebooklm source add "https://en.wikipedia.org/wiki/Artificial_intelligence"
```

The CLI auto-detects URLs, YouTube links, and local files:
- URLs: `source add "https://example.com/article"`
- YouTube: `source add "https://youtube.com/watch?v=..."`
- Files: `source add "./document.pdf"`

### Step 4: Chat with Your Sources

```bash
notebooklm ask "What are the key themes in this article?"
```

### Step 5: Generate a Podcast

```bash
notebooklm generate audio "Focus on the history and future predictions" --wait
```

This generates a podcast and waits for completion (takes 2-5 minutes).

### Step 6: Download the Result

```bash
notebooklm download audio ./my-podcast.mp3
```

## Using the Python API

```python
import asyncio
from notebooklm import NotebookLMClient

async def main():
    async with await NotebookLMClient.from_storage() as client:
        # List notebooks
        notebooks = await client.notebooks.list()
        print(f"Found {len(notebooks)} notebooks")

        # Create a notebook
        nb = await client.notebooks.create("API Test")
        print(f"Created: {nb.id}")

        # Add a source
        await client.sources.add_url(nb.id, "https://example.com")

        # Ask a question
        result = await client.chat.ask(nb.id, "Summarize this content")
        print(result.answer)

asyncio.run(main())
```

## Claude Code Integration

If you use [Claude Code](https://claude.ai/code), you can install a skill for natural language automation:

```bash
notebooklm skill install
```

After installation, Claude recognizes NotebookLM commands via:
- Explicit: `/notebooklm list`, `/notebooklm generate audio`
- Natural language: "Create a podcast about quantum computing", "Summarize these URLs"

Check installation status:
```bash
notebooklm skill status
```

## Next Steps

- [CLI Reference](cli-reference.md) - Complete command documentation
- [Python API](python-api.md) - Full API reference
- [Configuration](configuration.md) - Storage and environment settings
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

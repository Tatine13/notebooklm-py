# notebooklm-py (Fork)

> **🚨 Fork Status**: This is a maintained fork of `teng-lin/notebooklm-py` containing critical fixes for:
> - **Source Addition**: Fixed `add_url_source` and `add_file_source` parameters to match updated NotebookLM API (11-element array structure).
> - **Artifact Generation**: Improved monitoring and status parsing for artifacts (Audio, Infographic, etc.).
>
> **Install this version:**
> ```bash
> pip install git+https://github.com/Tatine13/notebooklm-py.git@main
> ```

**Unofficial Python library for automating Google NotebookLM.** Full programmatic access to NotebookLM's features—including capabilities the web UI doesn't expose—from Python or the command line.

[![PyPI version](https://img.shields.io/pypi/v/notebooklm-py.svg)](https://pypi.org/project/notebooklm-py/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/notebooklm-py/)
[![License](https://img.shields.io/pypi/l/notebooklm-py.svg)](https://github.com/teng-lin/notebooklm-py/blob/main/LICENSE)

## Why This Library?

Google NotebookLM is powerful, but:
1. **No official API** exists.
2. The web UI is manual and hard to automate.
3. Chatbots and agents can't easily interface with it.

`notebooklm-py` solves this by reverse-engineering the internal RPC protocol, giving you a robust Python client that behaves like a real user but running at code speed.

## Key Features

- **Auth & Session Management**: Handles cookies, headers, and token refresh automatically.
- **Full Source Support**: Add URLs (incl. YouTube), PDFs, text files, MP3s, and Google Drive docs.
- **Chat Interface**: Send queries and get referenced answers (citations included).
- **Artifact Generation**: Programmatically trigger Audio Overviews (podcasts), blog posts, FAQs, and study guides.
- **Rich Responses**: Parse complex RPC responses into clean Pydantic models.

## Installation

```bash
pip install notebooklm-py
```

For Playwright-based login (recommended for initial auth):

```bash
pip install "notebooklm-py[browser]"
playwright install chromium
```

## Quick Start

### 1. Login (One-time setup)

```python
from notebooklm.auth import GoogleAuth

# Opens browser for login, saves credentials to local storage
await GoogleAuth().login()
```

### 2. General Usage

```python
import asyncio
from notebooklm import NotebookLMClient

async def main():
    async with NotebookLMClient() as client:
        # Create a new notebook
        notebook = await client.create_notebook("My AI Research")
        print(f"Created notebook: {notebook.title} ({notebook.id})")

        # Add a source (e.g., Wikipedia)
        await client.add_source(notebook.id, "https://en.wikipedia.org/wiki/Artificial_intelligence")

        # Ask a question
        chat_response = await client.query(notebook.id, "Summarize the history of AI")
        print(chat_response.answer)

if __name__ == "__main__":
    asyncio.run(main())
```

See [examples/](examples/) for more advanced usage patterns.

## Development

Currently under active development. APIs may change.

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT

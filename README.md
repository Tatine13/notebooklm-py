# notebooklm-py

**Unofficial Python client for Google NotebookLM**

Automate Google NotebookLM programmatically. Create notebooks, add sources, chat with your content, and generate podcasts, videos, quizzes, and more - all via CLI or Python API.

[![PyPI version](https://badge.fury.io/py/notebooklm-py.svg)](https://badge.fury.io/py/notebooklm-py)
[![Python Version](https://img.shields.io/pypi/pyversions/notebooklm-py.svg)](https://pypi.org/project/notebooklm-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **⚠️ Beta Software**: This library uses reverse-engineered Google APIs that can change without notice. See [Troubleshooting](docs/troubleshooting.md) if you encounter issues.

## Installation

```bash
# Basic installation
pip install notebooklm-py

# With browser login support (required for first-time setup)
pip install "notebooklm-py[browser]"
playwright install chromium
```

## Quick Start

### CLI

```bash
# 1. Authenticate (opens browser)
notebooklm login

# 2. Create a notebook
notebooklm create "My Research"
notebooklm use <notebook_id>

# 3. Add sources
notebooklm source add "https://en.wikipedia.org/wiki/Artificial_intelligence"
notebooklm source add "./paper.pdf"

# 4. Chat
notebooklm ask "What are the key themes?"

# 5. Generate a podcast
notebooklm generate audio --wait
notebooklm download audio ./podcast.mp3
```

### Python API

```python
import asyncio
from notebooklm import NotebookLMClient

async def main():
    async with await NotebookLMClient.from_storage() as client:
        # List notebooks
        notebooks = await client.notebooks.list()

        # Create notebook and add source
        nb = await client.notebooks.create("Research")
        await client.sources.add_url(nb.id, "https://example.com")

        # Chat
        result = await client.chat.ask(nb.id, "Summarize this")
        print(result.answer)

        # Generate podcast
        status = await client.artifacts.generate_audio(nb.id)
        await client.artifacts.wait_for_completion(nb.id, status.task_id)

asyncio.run(main())
```

## Features

- **Notebooks**: Create, list, rename, delete, share
- **Sources**: URLs, YouTube, files (PDF/TXT/MD/DOCX), Google Drive, text
- **Chat**: Questions, conversation history, custom personas
- **Generation**: Audio (podcasts), video, slides, quizzes, flashcards, reports, infographics, mind maps
- **Research**: Web and Drive research agents
- **Downloads**: Audio, video, slides, infographics
- **Claude Code Integration**: Install as a skill for natural language automation

## Documentation

- **[Getting Started](docs/getting-started.md)** - Installation and first workflow
- **[CLI Reference](docs/cli-reference.md)** - Complete command documentation
- **[Python API](docs/python-api.md)** - Full API reference
- **[Configuration](docs/configuration.md)** - Storage and settings
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

### For Contributors

- **[Architecture](docs/contributing/architecture.md)** - Code structure
- **[Testing](docs/contributing/testing.md)** - Running and writing tests
- **[RPC Protocol](docs/contributing/rpc-protocol.md)** - Protocol reference
- **[Debugging](docs/contributing/debugging.md)** - Network capture guide

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*This is an unofficial library and is not affiliated with or endorsed by Google.*

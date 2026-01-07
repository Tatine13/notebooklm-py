# CLI Reference

Complete command reference for the `notebooklm` CLI.

## Command Structure

```
notebooklm [--storage PATH] [--version] <command> [OPTIONS] [ARGS]
```

**Global Options:**
- `--storage PATH` - Override the default storage location (`~/.notebooklm/storage_state.json`)
- `--version` - Show version and exit
- `--help` - Show help message

**Command Organization:**
- **Session commands** - Authentication and context management
- **Notebook commands** - CRUD operations on notebooks
- **Chat commands** - Querying and conversation management
- **Grouped commands** - `source`, `artifact`, `generate`, `download`, `note`

---

## Quick Reference

### Session Commands

| Command | Description | Example |
|---------|-------------|---------|
| `login` | Authenticate via browser | `notebooklm login` |
| `use <id>` | Set active notebook | `notebooklm use abc123` |
| `status` | Show current context | `notebooklm status` |
| `clear` | Clear current context | `notebooklm clear` |

### Notebook Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list` | List all notebooks | `notebooklm list` |
| `create <title>` | Create notebook | `notebooklm create "Research"` |
| `delete <id>` | Delete notebook | `notebooklm delete abc123` |
| `rename <title>` | Rename current notebook | `notebooklm rename "New Title"` |
| `share` | Configure sharing | `notebooklm share` |
| `featured` | List public notebooks | `notebooklm featured` |
| `summary` | Get AI summary | `notebooklm summary` |
| `analytics` | Get usage stats | `notebooklm analytics` |

### Chat Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ask <question>` | Ask a question | `notebooklm ask "What is this about?"` |
| `configure` | Set persona/mode | `notebooklm configure --mode learning-guide` |
| `history` | View/clear history | `notebooklm history --clear` |

### Source Commands (`notebooklm source <cmd>`)

| Command | Arguments | Options | Example |
|---------|-----------|---------|---------|
| `list` | - | - | `source list` |
| `add <content>` | URL/file/text | - | `source add "https://..."` |
| `add-drive <id> <title>` | Drive file ID | - | `source add-drive abc123 "Doc"` |
| `add-research <query>` | Search query | `--mode [fast\|deep]`, `--no-wait` | `source add-research "AI" --mode deep --no-wait` |
| `get <id>` | Source ID | - | `source get src123` |
| `rename <id> <title>` | Source ID, new title | - | `source rename src123 "New Name"` |
| `refresh <id>` | Source ID | - | `source refresh src123` |
| `delete <id>` | Source ID | - | `source delete src123` |

### Research Commands (`notebooklm research <cmd>`)

| Command | Arguments | Options | Example |
|---------|-----------|---------|---------|
| `status` | - | `--json` | `research status` |
| `wait` | - | `--timeout`, `--interval`, `--import-all`, `--json` | `research wait --import-all` |

### Generate Commands (`notebooklm generate <type>`)

| Command | Options | Example |
|---------|---------|---------|
| `audio [description]` | `--format`, `--length`, `--wait` | `generate audio "Focus on history"` |
| `video [description]` | `--style`, `--format`, `--wait` | `generate video "Explainer for kids"` |
| `slide-deck [description]` | `--format`, `--length`, `--wait` | `generate slide-deck` |
| `quiz [description]` | `--difficulty`, `--quantity`, `--wait` | `generate quiz --difficulty hard` |
| `flashcards [description]` | `--difficulty`, `--quantity`, `--wait` | `generate flashcards` |
| `infographic [description]` | `--orientation`, `--detail`, `--wait` | `generate infographic` |
| `data-table [description]` | `--wait` | `generate data-table` |
| `mind-map` | `--wait` | `generate mind-map` |
| `report [description]` | `--type`, `--wait` | `generate report --type study-guide` |

### Artifact Commands (`notebooklm artifact <cmd>`)

| Command | Arguments | Options | Example |
|---------|-----------|---------|---------|
| `list` | - | `--type` | `artifact list --type audio` |
| `get <id>` | Artifact ID | - | `artifact get art123` |
| `rename <id> <title>` | Artifact ID, title | - | `artifact rename art123 "Title"` |
| `delete <id>` | Artifact ID | - | `artifact delete art123` |
| `export <id>` | Artifact ID | - | `artifact export art123` |
| `poll <task_id>` | Task ID | - | `artifact poll task123` |
| `share` | - | `--enable/--disable` | `artifact share --enable` |
| `suggestions` | - | - | `artifact suggestions` |

### Download Commands (`notebooklm download <type>`)

| Command | Arguments | Options | Example |
|---------|-----------|---------|---------|
| `audio [path]` | Output path | - | `download audio ./podcast.mp3` |
| `video [path]` | Output path | - | `download video ./video.mp4` |
| `slide-deck [path]` | Output directory | - | `download slide-deck ./slides/` |
| `infographic [path]` | Output path | - | `download infographic ./info.png` |

### Note Commands (`notebooklm note <cmd>`)

| Command | Arguments | Options | Example |
|---------|-----------|---------|---------|
| `list` | - | - | `note list` |
| `create <content>` | Note content | - | `note create "My notes..."` |
| `get <id>` | Note ID | - | `note get note123` |
| `save <id>` | Note ID | - | `note save note123` |
| `rename <id> <title>` | Note ID, title | - | `note rename note123 "Title"` |
| `delete <id>` | Note ID | - | `note delete note123` |

### Skill Commands (`notebooklm skill <cmd>`)

Manage Claude Code skill integration.

| Command | Description | Example |
|---------|-------------|---------|
| `install` | Install/update skill to ~/.claude/skills/ | `skill install` |
| `status` | Check installation and version | `skill status` |
| `uninstall` | Remove skill | `skill uninstall` |
| `show` | Display skill content | `skill show` |

After installation, Claude Code recognizes NotebookLM commands via `/notebooklm` or natural language like "create a podcast about X".

---

## Detailed Command Reference

### Session: `login`

Authenticate with Google NotebookLM via browser.

```bash
notebooklm login
```

Opens a Chromium browser with a persistent profile. Log in to your Google account, then press Enter in the terminal to save the session.

### Session: `use`

Set the active notebook for subsequent commands.

```bash
notebooklm use <notebook_id>
```

Supports partial ID matching:
```bash
notebooklm use abc  # Matches abc123def456...
```

### Generate: `audio`

Generate an audio overview (podcast).

```bash
notebooklm generate audio [description] [OPTIONS]
```

**Options:**
- `--format [deep-dive|brief|critique|debate]` - Podcast format (default: deep-dive)
- `--length [short|default|long]` - Duration (default: default)
- `--language LANG` - Language code (default: en)
- `--wait` - Wait for generation to complete

**Examples:**
```bash
# Basic podcast
notebooklm generate audio

# Debate format with custom instructions
notebooklm generate audio "Compare the two main viewpoints" --format debate

# Wait for completion
notebooklm generate audio --wait
```

### Generate: `video`

Generate a video overview.

```bash
notebooklm generate video [description] [OPTIONS]
```

**Options:**
- `--format [explainer|brief]` - Video format
- `--style [auto|classic|whiteboard|kawaii|anime|watercolor|retro|heritage|paper-craft]` - Visual style
- `--language LANG` - Language code
- `--wait` - Wait for generation to complete

**Examples:**
```bash
# Kid-friendly explainer
notebooklm generate video "Explain for 5 year olds" --style kawaii

# Professional style
notebooklm generate video --style classic --wait
```

### Generate: `report`

Generate a text report (briefing doc, study guide, blog post, or custom).

```bash
notebooklm generate report [description] [OPTIONS]
```

**Options:**
- `--type [briefing-doc|study-guide|blog-post|custom]` - Report type

**Examples:**
```bash
notebooklm generate report --type study-guide
notebooklm generate report "Executive summary for stakeholders" --type briefing-doc
```

---

## Common Workflows

### Research → Podcast

Find information on a topic and create a podcast about it.

```bash
# 1. Create a notebook for this research
notebooklm create "Climate Change Research"
# Output: Created notebook: abc123

# 2. Set as active
notebooklm use abc123

# 3. Add a starting source
notebooklm source add "https://en.wikipedia.org/wiki/Climate_change"

# 4. Research more sources automatically (blocking - waits up to 5 min)
notebooklm source add-research "climate change policy 2024" --mode deep --import-all

# 5. Generate a podcast
notebooklm generate audio "Focus on policy solutions and future outlook" --format debate --wait

# 6. Download the result
notebooklm download audio ./climate-podcast.mp3
```

### Research → Podcast (Non-blocking with Subagent)

For LLM agents, use non-blocking mode to avoid timeout:

```bash
# 1-3. Create notebook and add initial source (same as above)
notebooklm create "Climate Change Research"
notebooklm use abc123
notebooklm source add "https://en.wikipedia.org/wiki/Climate_change"

# 4. Start deep research (non-blocking)
notebooklm source add-research "climate change policy 2024" --mode deep --no-wait
# Returns immediately

# 5. In a subagent, wait for research and import
notebooklm research wait --import-all --timeout 300
# Blocks until complete, then imports sources

# 6. Continue with podcast generation...
```

**Research commands:**
- `research status` - Check if research is in progress, completed, or not running
- `research wait --import-all` - Block until research completes, then import sources

### Document Analysis → Study Materials

Upload documents and create study materials.

```bash
# 1. Create notebook
notebooklm create "Exam Prep"
notebooklm use <id>

# 2. Add your documents
notebooklm source add "./textbook-chapter.pdf"
notebooklm source add "./lecture-notes.pdf"

# 3. Get a summary
notebooklm summary

# 4. Generate study materials
notebooklm generate quiz --difficulty hard --wait
notebooklm generate flashcards --wait
notebooklm generate report --type study-guide --wait

# 5. Ask specific questions
notebooklm ask "Explain the key concepts in chapter 3"
notebooklm ask "What are the most likely exam topics?"
```

### YouTube → Quick Summary

Turn a YouTube video into notes.

```bash
# 1. Create notebook and add video
notebooklm create "Video Notes"
notebooklm use <id>
notebooklm source add "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. Get summary
notebooklm summary

# 3. Ask questions
notebooklm ask "What are the main points?"
notebooklm ask "Create bullet point notes"

# 4. Generate a quick briefing doc
notebooklm generate report --type briefing-doc --wait
```

### Bulk Import

Add multiple sources at once.

```bash
# Set active notebook
notebooklm use <id>

# Add multiple URLs
notebooklm source add "https://example.com/article1"
notebooklm source add "https://example.com/article2"
notebooklm source add "https://example.com/article3"

# Add multiple local files (use a loop)
for f in ./papers/*.pdf; do
  notebooklm source add "$f"
done
```

---

## Tips for LLM Agents

When using this CLI programmatically:

1. **Always set context first**: Use `notebooklm use <id>` before running commands that operate on a notebook.

2. **Use `--wait` for generation**: Generation commands return immediately by default. Add `--wait` to block until complete.

3. **Partial IDs work**: `notebooklm use abc` matches any notebook ID starting with "abc".

4. **Check status**: Use `notebooklm status` to see the current active notebook and conversation.

5. **Auto-detection**: `source add` auto-detects content type:
   - URLs starting with `http` → web source
   - YouTube URLs → video transcript extraction
   - File paths → file upload

6. **Error handling**: Commands exit with non-zero status on failure. Check stderr for error messages.

7. **Deep research**: Use `--no-wait` with `source add-research --mode deep` to avoid blocking. Then use `research wait --import-all` in a subagent to wait for completion.

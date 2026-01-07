---
name: notebooklm
description: Automate Google NotebookLM - create notebooks, add sources, generate podcasts/videos/quizzes, download artifacts. Activates on explicit /notebooklm or intent like "create a podcast about X"
---

# NotebookLM Automation

Automate Google NotebookLM: create notebooks, add sources, chat with content, generate artifacts (podcasts, videos, quizzes), and download results.

## Prerequisites

**IMPORTANT:** Before using any command, you MUST authenticate:

```bash
notebooklm login          # Opens browser for Google OAuth
notebooklm list           # Verify authentication works
```

If commands fail with authentication errors, re-run `notebooklm login`.

## When This Skill Activates

**Explicit:** User says "/notebooklm", "use notebooklm", or mentions the tool by name

**Intent detection:** Recognize requests like:
- "Create a podcast about [topic]"
- "Summarize these URLs/documents"
- "Generate a quiz from my research"
- "Turn this into an audio overview"
- "Add these sources to NotebookLM"

## Autonomy Rules

**Run automatically (no confirmation):**
- `notebooklm status` - check context
- `notebooklm list` - list notebooks
- `notebooklm source list` - list sources
- `notebooklm artifact list` - list artifacts
- `notebooklm artifact wait` - wait for completion (in subagent context)
- `notebooklm research status` - check research status
- `notebooklm research wait` - wait for research (in subagent context)
- `notebooklm use <id>` - set context
- `notebooklm create` - create notebook
- `notebooklm ask "..."` - chat queries
- `notebooklm source add` - add sources

**Ask before running:**
- `notebooklm delete` - destructive
- `notebooklm generate *` - long-running, may fail
- `notebooklm download *` - writes to filesystem
- `notebooklm artifact wait` - long-running (when in main conversation)
- `notebooklm research wait` - long-running (when in main conversation)

## Quick Reference

| Task | Command |
|------|---------|
| Authenticate | `notebooklm login` |
| List notebooks | `notebooklm list` |
| Create notebook | `notebooklm create "Title"` |
| Set context | `notebooklm use <notebook_id>` |
| Show context | `notebooklm status` |
| Add URL source | `notebooklm source add "https://..."` |
| Add file | `notebooklm source add ./file.pdf` |
| Add YouTube | `notebooklm source add "https://youtube.com/..."` |
| List sources | `notebooklm source list` |
| Web research (fast) | `notebooklm source add-research "query"` |
| Web research (deep) | `notebooklm source add-research "query" --mode deep --no-wait` |
| Check research status | `notebooklm research status` |
| Wait for research | `notebooklm research wait --import-all` |
| Chat | `notebooklm ask "question"` |
| Generate podcast | `notebooklm generate audio "instructions"` |
| Generate video | `notebooklm generate video "instructions"` |
| Generate quiz | `notebooklm generate quiz` |
| Check artifact status | `notebooklm artifact list` |
| Wait for completion | `notebooklm artifact wait <artifact_id>` |
| Download audio | `notebooklm download audio ./output.mp3` |
| Download video | `notebooklm download video ./output.mp4` |
| Delete notebook | `notebooklm notebook delete <id>` |

**Partial IDs:** Use short IDs (first 6-8 chars) instead of full UUIDs. Example: `notebooklm use abc123` matches `abc123de-1234-...`

## Generation Types

| Type | Command | Downloadable |
|------|---------|--------------|
| Podcast | `generate audio` | Yes (.mp3) |
| Video | `generate video` | Yes (.mp4) |
| Slides | `generate slide-deck` | Yes (.pdf) |
| Infographic | `generate infographic` | Yes (.png) |
| Quiz | `generate quiz` | No (view in UI) |
| Flashcards | `generate flashcards` | No (view in UI) |
| Mind Map | `generate mind-map` | No (view in UI) |
| Data Table | `generate data-table` | No (export to Sheets) |
| Report | `generate report` | No (export to Docs) |

## Common Workflows

### Research to Podcast (Interactive)
**Time:** 5-10 minutes total

1. `notebooklm create "Research: [topic]"`
2. `notebooklm source add` for each URL/document
3. `notebooklm generate audio "Focus on [specific angle]"` (confirm when asked)
4. Note the artifact ID returned
5. Check `notebooklm artifact list` later for status
6. `notebooklm download audio ./podcast.mp3` when complete (confirm when asked)

### Research to Podcast (Automated with Subagent)
**Time:** 5-10 minutes, but continues in background

When user wants full automation (generate and download when ready):

1. Create notebook and add sources as usual
2. Run `notebooklm generate audio "..."` → returns artifact_id
3. **Spawn a subagent** to wait and download:
   ```bash
   # Subagent runs:
   notebooklm artifact wait <artifact_id> --timeout 600
   notebooklm download audio ./podcast.mp3 -a <artifact_id>
   ```
4. Main conversation can continue while subagent waits

**Benefits:** Non-blocking, user can do other work, automatic download on completion

### Document Analysis
**Time:** 1-2 minutes

1. `notebooklm create "Analysis: [project]"`
2. `notebooklm source add ./doc.pdf` (or URLs)
3. `notebooklm ask "Summarize the key points"`
4. `notebooklm ask "What are the main arguments?"`
5. Continue chatting as needed

### Bulk Import
**Time:** Varies by source count

1. `notebooklm create "Collection: [name]"`
2. Add multiple sources:
   ```bash
   notebooklm source add "https://url1.com"
   notebooklm source add "https://url2.com"
   notebooklm source add ./local-file.pdf
   ```
3. `notebooklm source list` to verify

**Source limits:** Max 50 sources per notebook
**Supported types:** PDFs, YouTube URLs, web URLs, Google Docs, text files

### Deep Web Research (Subagent Pattern)
**Time:** 2-5 minutes, runs in background

Deep research finds and analyzes web sources on a topic. Use non-blocking mode with a subagent:

1. Create notebook: `notebooklm create "Research: [topic]"`
2. Start deep research (non-blocking):
   ```bash
   notebooklm source add-research "topic query" --mode deep --no-wait
   ```
3. **Spawn a subagent** to wait and import:
   ```bash
   # Subagent runs:
   notebooklm research wait --import-all --timeout 300
   ```
4. Main conversation continues while subagent waits
5. When subagent completes, sources are imported automatically

**Alternative (blocking):** For simple cases, omit `--no-wait`:
```bash
notebooklm source add-research "topic" --mode deep --import-all
# Blocks for up to 5 minutes
```

**Research modes:**
- `--mode fast`: Quick search, returns in seconds (default)
- `--mode deep`: Thorough analysis, takes 2-5 minutes

**Research sources:**
- `--from web`: Search the web (default)
- `--from drive`: Search Google Drive

## Output Style

**Progress updates:** Brief status for each step
- "Creating notebook 'Research: AI'..."
- "Adding source: https://example.com..."
- "Starting audio generation... (task ID: abc123)"

**Fire-and-forget for long operations:**
- Start generation, return artifact ID immediately
- Do NOT poll or wait in main conversation - generation takes 2-5 minutes
- User checks status manually, OR use subagent with `artifact wait`

**JSON output:** Use `--json` flag for machine-readable output:
```bash
notebooklm list --json
notebooklm source list --json
notebooklm artifact list --json
```

## Error Handling

**On failure, offer the user a choice:**
1. Retry the operation
2. Skip and continue with something else
3. Investigate the error

**Error decision tree:**

| Error | Cause | Action |
|-------|-------|--------|
| Auth/cookie error | Session expired | Run `notebooklm login` |
| "No notebook context" | Context not set | Run `notebooklm use <id>` |
| "No result found for RPC ID" | Rate limiting | Wait 5-10 min, retry |
| `GENERATION_FAILED` | Google rate limit | Wait and retry later |
| Download fails | Generation incomplete | Check `artifact list` for status |
| Invalid notebook/source ID | Wrong ID | Run `notebooklm list` to verify |
| RPC protocol error | Google changed APIs | May need CLI update |

## Known Limitations

**Rate limiting:** Audio, video, quiz, flashcards, infographic, and slides generation may fail due to Google's rate limits. This is an API limitation, not a bug.

**Reliable operations:** These always work:
- Notebooks (list, create, delete, rename)
- Sources (add, list, delete)
- Chat/queries
- Mind-map, study-guide, FAQ, data-table generation

**Unreliable operations:** These may fail with rate limiting:
- Audio (podcast) generation
- Video generation
- Quiz and flashcard generation
- Infographic and slides generation

**Workaround:** If generation fails:
1. Check status: `notebooklm artifact list`
2. Retry after 5-10 minutes
3. Use the NotebookLM web UI as fallback

**Generation time:** Audio takes 2-5 minutes, video takes longer. Do not wait - use fire-and-forget pattern.

## Troubleshooting

```bash
notebooklm --help              # Main commands
notebooklm notebook --help     # Notebook management
notebooklm source --help       # Source management
notebooklm research --help     # Research status/wait
notebooklm generate --help     # Content generation
notebooklm artifact --help     # Artifact management
notebooklm download --help     # Download content
```

**Re-authenticate:** `notebooklm login`
**Check version:** `notebooklm --version`
**Update skill:** `notebooklm skill install`

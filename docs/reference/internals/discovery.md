# Reverse Engineering Discovery Notes

**Status:** Active
**Last Updated:** 2026-01-06

This document consolidates reverse engineering notes from UI discovery sessions used to build `notebooklm-client`. These notes document how RPC methods, payload structures, and UI interactions were discovered.

---

## Table of Contents

1. [Overview](#overview)
2. [Network Traffic Analysis](#network-traffic-analysis)
3. [Notebook List Discovery](#notebook-list-discovery)
4. [Source Panel Discovery](#source-panel-discovery)
5. [Chat Panel Discovery](#chat-panel-discovery)
6. [Studio Panel Discovery](#studio-panel-discovery)
7. [Adding New RPC Methods](#adding-new-rpc-methods)

---

## Overview

NotebookLM uses Google's `batchexecute` RPC protocol - a proprietary RPC-over-HTTP mechanism. Key concepts:

| Term | Description |
|------|-------------|
| **batchexecute** | Google's internal RPC protocol endpoint |
| **RPC ID** | 6-char identifier (e.g., `wXbhsf`, `CCqFvf`) |
| **f.req** | URL-encoded JSON payload |
| **at** | CSRF token (SNlM0e value) |
| **Anti-XSSI** | `)]}'` prefix on responses |

### Protocol Flow

```
1. Build request: [[[rpc_id, json_params, null, "generic"]]]
2. Encode to f.req parameter
3. POST to /_/LabsTailwindUi/data/batchexecute
4. Strip )]}' prefix from response
5. Parse chunked JSON, extract result
```

---

## Network Traffic Analysis

### Tools Required

- Chrome DevTools (Network tab, filter by `batchexecute`)
- A text editor for payload analysis
- Python for testing discovered methods

### Capture Process

1. Open DevTools → Network tab
2. Filter: `batchexecute`
3. Perform action in NotebookLM UI
4. Find the corresponding request
5. Examine:
   - URL query params: `rpcids=METHOD_ID`
   - Request body: `f.req=...` (URL-encoded)
   - Response: Strip prefix, parse JSON

### Decoding Payloads

The `f.req` parameter is URL-encoded JSON. Decode it:

```python
import urllib.parse
import json

encoded = "..."  # From network capture
decoded = urllib.parse.unquote(encoded)
data = json.loads(decoded)
# data is now: [[[rpc_id, params_json, null, "generic"]]]
```

### Response Format

Responses are chunked with byte counts:

```
)]}'

123
["wrb.fr","wXbhsf","[...]",null,null,null,"generic"]

45
["di",42]
```

Extract the `wrb.fr` chunk matching your RPC ID.

---

## Notebook List Discovery

**URL:** `https://notebooklm.google.com/`

### Discovered Methods

| RPC ID | Method | Purpose |
|--------|--------|---------|
| `wXbhsf` | LIST_NOTEBOOKS | List all notebooks |
| `CCqFvf` | CREATE_NOTEBOOK | Create new notebook |
| `WWINqb` | DELETE_NOTEBOOK | Delete notebook |
| `s0tc2d` | RENAME_NOTEBOOK | Rename/configure notebook |

### LIST_NOTEBOOKS Payload

```python
params = [None, 1, None, [2]]
```

Response structure:
```
[[notebook_id, title, None, [[timestamp]], sources_count, ...], ...]
```

### CREATE_NOTEBOOK Payload

```python
params = [title, None, None, [2], [1]]
```

---

## Source Panel Discovery

**Context:** Inside a notebook, the source panel shows all sources.

### Discovered Methods

| RPC ID | Method | Purpose |
|--------|--------|---------|
| `izAoDd` | ADD_SOURCE | Add URL/text/Drive source |
| `o4cbdc` | ADD_SOURCE_FILE | Register file upload |
| `tGMBJ` | DELETE_SOURCE | Remove source |
| `FLmJqe` | REFRESH_SOURCE | Re-fetch URL content |

### ADD_SOURCE (URL)

URL at position 7, same structure as YouTube.
```python
source_data = [None, None, None, None, None, None, None, [url], None, None, 1]
settings = [1, None, None, None, None, None, None, None, None, None, [1]]
params = [[[source_data]], notebook_id, [2], settings]
```

### ADD_SOURCE (YouTube)

Same structure as regular URL.
```python
source_data = [None, None, None, None, None, None, None, [url], None, None, 1]
settings = [1, None, None, None, None, None, None, None, None, None, [1]]
params = [[[source_data]], notebook_id, [2], settings]
```

### ADD_SOURCE (Text)

```python
source_data = [None, [title, content], None, None, None, None, None, None]
params = [[[source_data]], notebook_id, [2], None, None]
```

### ADD_SOURCE (Google Drive)

```python
source_data = [
    [file_id, mime_type, 1, title],
    None, None, None, None, None, None, None, None, None, 1
]
settings = [1, None, None, None, None, None, None, None, None, None, [1]]
params = [[[source_data]], notebook_id, [2], settings]
```

---

## Chat Panel Discovery

**Context:** The chat interface in a notebook.

### Discovered Methods

| RPC ID | Method | Purpose |
|--------|--------|---------|
| `VfAZjd` | SUMMARIZE | Get notebook summary |
| `tr032e` | GET_SOURCE_GUIDE | Get source-specific summary |

### Query Endpoint

Chat uses a different endpoint: `/_/LabsTailwindUi/batchexecute` (streaming)

The streaming response uses Server-Sent Events format with chunked JSON.

### Configure Chat

Uses `s0tc2d` (same as rename) with different payload structure:

```python
params = [
    notebook_id,
    [[
        None, None, None, None, None, None, None,
        [[goal_code, custom_prompt], [response_length_code]]
    ]]
]
```

Goal codes: 1=Default, 2=Custom, 3=Learning Guide
Length codes: 1=Default, 4=Longer, 5=Shorter

---

## Studio Panel Discovery

**Context:** The "Studio" tab for generating artifacts.

### Discovered Methods

| RPC ID | Method | Purpose |
|--------|--------|---------|
| `R7cb6c` | CREATE_ARTIFACT | Unified artifact creation |
| `gArtLc` | POLL_STUDIO | Check status / list artifacts |
| `V5N4be` | DELETE_STUDIO | Delete artifact |
| `yyryJe` | ACT_ON_SOURCES | Generate mind map |

### CREATE_ARTIFACT (Unified)

All artifacts use `R7cb6c` with different type codes:

```python
# Type codes
AUDIO = 1
REPORT = 2
VIDEO = 3
QUIZ_FLASHCARD = 4
INFOGRAPHIC = 7
SLIDES = 8
DATA_TABLE = 9
```

### Audio Generation

```python
params = [
    [2], notebook_id, [
        None, None, 1,  # type=1 for audio
        source_ids_triple,  # [[[s1]], [[s2]]]
        None, None,
        [None, [
            instructions,
            length_code,
            None,
            source_ids_double,  # [[s1], [s2]]
            language,
            None,
            format_code
        ]]
    ]
]
```

Format codes: 1=Deep Dive, 2=Brief, 3=Critique, 4=Debate
Length codes: 1=Short, 2=Default, 3=Long

### Video Generation

```python
params = [
    [2], notebook_id, [
        None, None, 3,  # type=3 for video
        source_ids_triple,
        None, None, None, None,
        [None, None, [
            source_ids_double,
            language,
            instructions,
            None,
            format_code,  # 1=Explainer, 2=Brief
            style_code    # 1-10 for different styles
        ]]
    ]
]
```

### Polling Status

```python
params = [task_id, notebook_id, [2]]
```

Status codes: 1=In Progress, 3=Completed, 4=Failed

---

## Adding New RPC Methods

When Google adds new features:

1. **Capture traffic**
   - Open DevTools Network tab
   - Filter by `batchexecute`
   - Perform the new action in UI
   - Find the request

2. **Identify RPC ID**
   - Check URL: `rpcids=NEW_ID`
   - Note the 6-character code

3. **Decode payload**
   - Copy `f.req` value
   - URL-decode and parse JSON
   - Document the nested structure

4. **Analyze response**
   - Strip `)]}'` prefix
   - Parse chunked format
   - Find the `wrb.fr` chunk

5. **Implement**
   - Add to `rpc/types.py`: `NEW_METHOD = "NEW_ID"`
   - Add client method using `_rpc_call(RPCMethod.NEW_METHOD, params)`

6. **Test**
   - Write unit test with mocked response
   - Write E2E test (if safe to run)

### Common Pitfalls

- **Position matters**: Params are position-sensitive arrays
- **Nesting depth**: Source IDs have varying nesting (single, double, triple, quad)
- **Null placeholders**: Many `None` values are required placeholders
- **Response parsing**: Different methods return data at different positions

---

## Historical Discovery Files

The following detailed discovery documents were used during initial development:

- `NOTEBOOK_LIST_DISCOVERY.md` - Home page UI selectors and notebook CRUD
- `SOURCE_PANEL_DISCOVERY.md` - Source management UI and methods
- `CHAT_PANEL_DISCOVERY.md` - Chat interface and streaming responses
- `STUDIO_PANEL_DISCOVERY.md` - Artifact generation UI and methods
- `NETWORK_TRAFFIC_ANALYSIS.md` - Traffic capture methodology

These files contain exhaustive UI selector mappings and step-by-step discovery logs that may be useful for debugging or extending the library.

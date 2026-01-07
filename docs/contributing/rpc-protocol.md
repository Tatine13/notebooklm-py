# RPC Reference: NotebookLM Internal API

**Status:** Active
**Last Updated:** 2026-01-06

This document provides a comprehensive technical reference for the reverse-engineered RPC (Remote Procedure Call) mechanism used by Google NotebookLM. It is intended for developers who want to understand the underlying protocol or contribute to the library.

## 1. Base Endpoint and Request Format

### Endpoint URL
All standard RPC operations are sent to Google's `batchexecute` endpoint:
`https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute`

### Request Format
The API expects a form-encoded POST body with an `f.req` parameter containing a triple-nested JSON array:

```python
# Triple-nested structure
rpc_request = [[[
    "RPC_ID",             # The 6-character method ID
    "JSON_PARAMS_STRING", # Method parameters as a JSON-encoded string
    None,                 # Always null
    "generic"             # Always "generic"
]]]
```

The parameters inside `JSON_PARAMS_STRING` are often deeply nested arrays where positions are critical.

### URL Query Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| `rpcids` | `MethodID` | The method ID(s) being called (e.g., `wXbhsf`) |
| `f.sid` | `SessionID` | The `FdrFJe` session identifier |
| `bl` | `BuildLabel` | Internal Google build version (e.g., `boq_labs-tailwind-frontend_...`) |
| `hl` | `en` | Language code |
| `rt` | `c` | **Chunked** response mode (required for parsing) |
| `source-path` | `/notebook/ID` | Contextual path for the operation |

### Response Format
Google uses a security-hardened, chunked format:
1. **Anti-XSSI Prefix**: `)]}'` followed by a newline.
2. **Chunked Body**: Alternating lines of `byte_count` (integer) and `json_payload`.
3. **Success Marker**: Result data is wrapped in a `["wrb.fr", "MethodID", "RESULT_JSON"]` array.
4. **Error Marker**: Errors appear as `["er", "MethodID", "ERROR_CODE_OR_MESSAGE"]`.

---

## 2. Known RPC IDs Table

| RPC ID | Enum Name | Purpose | Params Structure |
|--------|-----------|---------|------------------|
| `wXbhsf` | `LIST_NOTEBOOKS` | List all user notebooks | `[None, 1, None, [2]]` |
| `CCqFvf` | `CREATE_NOTEBOOK` | Create a new notebook | `[title, None, None, [2], [1]]` |
| `rLM1Ne` | `GET_NOTEBOOK` | Get notebook details/sources | `[nb_id, None, [2], None, 0]` |
| `s0tc2d` | `RENAME_NOTEBOOK` | Rename or configure chat | `[nb_id, [[...]]]` (See Section 3) |
| `WWINqb` | `DELETE_NOTEBOOK` | Delete a notebook | `[[nb_id], [2]]` |
| `izAoDd` | `ADD_SOURCE` | Add URL/Text/Drive source | `[[[data]], nb_id, [2], settings]` |
| `o4cbdc` | `ADD_SOURCE_FILE` | Register uploaded file | `[[[filename]], nb_id, [2], [1, ...]]` |
| `tGMBJ` | `DELETE_SOURCE` | Remove source from notebook | `[[[source_id]]]` |
| `hizoJc` | `GET_SOURCE` | Get specific source details | `[source_id]` |
| `FLmJqe` | `REFRESH_SOURCE` | Update source content | `[None, [source_id], [2]]` |
| `yR9Yof` | `CHECK_SOURCE_FRESHNESS` | Check for stale sources | `[None, [source_id], [2]]` |
| `VfAZjd` | `SUMMARIZE` | Get AI summary/topics | `[nb_id, [2]]` |
| `tr032e` | `GET_SOURCE_GUIDE` | Get source-specific guide | `[[[[source_id]]]]` |
| `ciyUvf` | `GET_SUGGESTED_REPORTS` | Get report suggestions | `[[2], nb_id, [[sid1], [sid2]]]` |
| `R7cb6c` | `CREATE_ARTIFACT` | **Unified** studio creation | `[[2], nb_id, [None, None, type, ...]]` |
| `gArtLc` | `POLL_STUDIO` | Poll status or list artifacts | `[task_id, nb_id, [2]]` |
| `V5N4be` | `DELETE_STUDIO` | Delete studio artifact | `[[2], artifact_id]` |
| `yyryJe` | `ACT_ON_SOURCES` | Generate Mind Map / Actions | `[source_ids, ..., ["action", ...]]` |
| `CYK0Xb` | `CREATE_NOTE` | Create note or save Mind Map | `[nb_id, data, title, [2]]` |
| `cFji9` | `GET_NOTES` | List all notes and Mind Maps | `[nb_id]` |
| `cYAfTb` | `UPDATE_NOTE` | Save content to text note | `[nb_id, note_id, [[[content, title, ...]]]]` |
| `AH0mwd` | `DELETE_NOTE` | Clear/Delete note content | `[nb_id, None, [note_id]]` |
| `rc3d8d` | `RENAME_ARTIFACT` | Rename note/data table | `[[art_id, new_title], [["title"]]]` |
| `Krh3pd` | `EXPORT_ARTIFACT` | Export to Google Docs/Sheets | `[None, art_id, content, title, type]` |
| `Ljjv0c` | `START_FAST_RESEARCH` | Start web research (Fast) | `[[query, type], None, 1, nb_id]` |
| `QA9ei` | `START_DEEP_RESEARCH` | Start web research (Deep) | `[None, [1], [query, type], 5, nb_id]` |
| `e3bVqc` | `POLL_RESEARCH` | Poll research agent status | `[None, None, nb_id]` |
| `LBwxtb` | `IMPORT_RESEARCH` | Import findings to notebook | `[None, [1], task_id, nb_id, sources]` |

---

## 3. `s0tc2d` - Notebook Update RPC (Multi-Purpose)

This RPC is used for modifying notebook-level settings.

### Rename Notebook
```python
params = [
    notebook_id,
    [[None, None, None, [None, "New Title"]]]
]
```

### Configure Chat Settings
Controls the AI persona and response style.

```python
params = [
    notebook_id,
    [[
        None, None, None, None, None, None, None,
        [[goal_code, custom_prompt], [response_length_code]]
    ]]
]
```

#### Goal Codes
| Code | Name | Description |
|------|------|-------------|
| `1` | Default | General research and brainstorming |
| `2` | Custom | Uses `custom_prompt` (up to 10k chars) |
| `3` | Learning Guide | Educational focus, learning-oriented responses |

#### Response Length Codes
| Code | Name | Description |
|------|------|-------------|
| `1` | Default | Standard response length |
| `4` | Longer | Verbose, detailed responses |
| `5` | Shorter | Concise, brief responses |

---

## 4. Source Types (via `izAoDd` RPC)

All sources are added using the `izAoDd` RPC ID, but the internal `source_data` structure varies significantly by type.

### Regular Website URL
URL goes at position 7 with trailing `1`, same structure as YouTube.
```python
source_data = [None, None, None, None, None, None, None, [url], None, None, 1]
settings = [1, None, None, None, None, None, None, None, None, None, [1]]
params = [[[source_data]], notebook_id, [2], settings]
```

### YouTube URL
Same structure as regular URL - URL at position 7 with trailing `1`.
```python
source_data = [None, None, None, None, None, None, None, [url], None, None, 1]
settings = [1, None, None, None, None, None, None, None, None, None, [1]]
params = [[[source_data]], notebook_id, [2], settings]
```

### Pasted Text Source
```python
source_data = [None, [title, text_content], None, None, None, None, None, None]
params = [[[source_data]], notebook_id, [2], None, None]
```

### Google Drive Source
```python
# Drive structure: [[file_id, mime_type, 1, title], null x9, 1]
source_data = [
    [file_id, mime_type, 1, title],
    None, None, None, None, None, None, None, None, None, 1
]
settings = [1, None, None, None, None, None, None, None, None, None, [1]]
params = [[[source_data]], notebook_id, [2], settings]
```

#### Common Drive MIME Types
- `application/vnd.google-apps.document` (Docs)
- `application/vnd.google-apps.presentation` (Slides)
- `application/vnd.google-apps.spreadsheet` (Sheets)
- `application/pdf` (PDF)

---

## 5. Studio RPCs (`R7cb6c` - Unified Create)

Almost all Studio content (Audio, Video, Quizzes, etc.) is triggered via the `R7cb6c` method.

### Audio Overview (type=1)
Generates a two-host podcast.
```python
params = [
    [2], notebook_id, [
        None, None, 1,          # Content Type 1
        source_ids_triple,      # [[[sid1]], [[sid2]]]
        None, None,
        [None, [
            instructions,       # String
            length_code,        # AudioLength (1-3)
            None,
            source_ids_double,  # [[sid1], [sid2]]
            language,           # "en"
            None,
            format_code         # AudioFormat (1-4)
        ]]
    ]
]
```
- **Audio Formats**: 1=Deep Dive, 2=Brief, 3=Critique, 4=Debate
- **Audio Lengths**: 1=Short, 2=Default, 3=Long

### Video Overview (type=3)
Generates an explainer video.
```python
params = [
    [2], notebook_id, [
        None, None, 3,          # Content Type 3
        source_ids_triple,
        None, None, None, None,
        [None, None, [
            source_ids_double,
            language,
            instructions,
            None,
            format_code,        # VideoFormat (1-2)
            style_code          # VideoStyle (1-10)
        ]]
    ]
]
```
- **Video Formats**: 1=Explainer, 2=Brief
- **Video Styles**: 1=Auto, 2=Custom, 3=Classic, 4=Whiteboard, 5=Kawaii, 6=Anime, 7=Watercolor, 8=Retro Print, 9=Heritage, 10=Paper Craft

### Report (type=2)
Used for Briefing Docs, Study Guides, and Blog Posts.
```python
params = [
    [2], notebook_id, [
        None, None, 2,          # Content Type 2
        source_ids_triple,
        None, None, None,
        [None, [
            title, description, None,
            source_ids_double, language, prompt,
            None, True
        ]]
    ]
]
```

### Quiz & Flashcards (type=4)
- **Quiz**: Variant code `2`
- **Flashcards**: Variant code `1`

```python
params = [
    [2], notebook_id, [
        None, None, 4,          # Content Type 4
        source_ids_triple,
        ...,
        [None, [
            variant_code,       # 1=Flashcard, 2=Quiz
            None, instructions,
            ...,
            [arg1, arg2]         # [Quantity, Difficulty] for Quiz
                                 # [Difficulty, Quantity] for Flashcards
        ]]
    ]
]
```
- **Quantity**: 1=Fewer, 2=Standard/More
- **Difficulty**: 1=Easy, 2=Medium, 3=Hard

### Infographic (type=7)
```python
# Metadata at index 14
metadata = [None, [instructions, language, None, orientation, detail]]
params = [[2], notebook_id, [None, None, 7, source_ids_triple, ..., metadata]]
```
- **Orientations**: 1=Landscape, 2=Portrait, 3=Square
- **Detail Level**: 1=Concise, 2=Standard, 3=Detailed

### Slide Deck (type=8)
```python
# Metadata at index 16
metadata = [[instructions, language, format, length]]
params = [[2], notebook_id, [None, None, 8, source_ids_triple, ..., metadata]]
```
- **Formats**: 1=Detailed, 2=Presenter
- **Lengths**: 1=Default, 2=Short

### Data Table (type=9)
```python
# Metadata at index 18
metadata = [None, [instructions, language]]
params = [[2], notebook_id, [None, None, 9, source_ids_triple, ..., metadata]]
```

---

## 6. Research RPCs

### Start Fast Research (`Ljjv0c`)
```python
params = [[query, source_type], None, 1, notebook_id]
```
- **source_type**: 1=Web, 2=Drive

### Start Deep Research (`QA9ei`)
```python
params = [None, [1], [query, source_type], 5, notebook_id]
```

### Import Research (`LBwxtb`)
```python
# sources is a list of [None, None, [url, title], ..., 2]
params = [None, [1], task_id, notebook_id, sources]
```

---

## 7. AI Summary RPCs

### Get Summary (`VfAZjd`)
Returns the general notebook summary and suggested report topics.
```python
params = [notebook_id, [2]]
```

### Get Source Guide (`tr032e`)
Returns summary and keywords for a specific source.
**Crucial**: The source ID must be quad-nested.
```python
params = [[[[source_id]]]]
```

---

## 8. Mind Map RPCs

### Generate Mind Map (`yyryJe`)
Uses the `ACT_ON_SOURCES` RPC with specific action metadata.
```python
params = [
    source_ids_triple,
    None, None, None, None,
    ["interactive_mindmap", [["[CONTEXT]", ""]], ""],
    None, [2, None, [1]]
]
```

---

## 9. Polling and Status (`gArtLc`)

Used to check the progress of Studio artifacts (Audio, Video, etc.).
```python
params = [task_id, notebook_id, [2]]
```

### Status Codes
- `1`: **In Progress**
- `3`: **Completed**
- `4`: **Failed**

---

## 10. File Upload Protocol

Native file uploads use a 3-step resumable protocol.

1.  **Register (`o4cbdc`)**: Pre-register the filename to get a `SOURCE_ID`.
    `[[[filename]], nb_id, [2], [1, None, ..., [1]]]`
2.  **Start session**: POST to `UPLOAD_URL` with `x-goog-upload-command: start` and file metadata to get a unique upload URL.
3.  **Transfer**: POST content to the unique upload URL with `x-goog-upload-command: upload, finalize`.

---

## 11. Response Parsing

All responses require stripping the `)]}'` prefix before parsing as JSON.

Success result extraction:
- Locate the chunk containing `["wrb.fr", "MethodID", "..."]`.
- The third element is the payload, often a JSON-encoded string that must be decoded again.

Error extraction:
- Locate `["er", "MethodID", error_info]`.
- `error_info` can be a numeric code or an error message string.

---

## 12. Source ID Nesting Patterns

Parameter arrays are extremely sensitive to nesting depth for Source IDs:

-   **Single**: `["src_id"]` (e.g., Refresh Source)
-   **Double**: `[[sid1], [sid2]]` (e.g., Suggested Reports)
-   **Triple**: `[[[sid1]], [[sid2]]]` (e.g., Artifact Generation)
-   **Quad**: `[[[[src_id]]]]` (e.g., Source Guide)

---

## 13. Essential Cookies

The following cookies are mandatory for authenticated requests:
- `SID`, `HSID`, `SSID`, `APISID`, `SAPISID`
- `__Secure-1PSID`, `__Secure-3PSID`
- `__Secure-1PAPISID`, `__Secure-3PAPISID`

---

## 14. Token Extraction

Both tokens are found in the `WIZ_global_data` object in the page HTML:
- **CSRF Token**: Key `SNlM0e` (Used in POST body as `at`).
- **Session ID**: Key `FdrFJe` (Used in URL as `f.sid`).

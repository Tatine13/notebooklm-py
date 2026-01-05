# Phase 1: RPC Layer Encapsulation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan.

**Goal:** Extract "magic list" construction and complex response parsing from `api_client.py` into dedicated `builders.py` and `parsers.py` modules.

**Architecture:**
- `src/notebooklm/rpc/builders.py`: Pure functions returning `list[Any]` for RPC payloads.
- `src/notebooklm/rpc/parsers.py`: Pure functions parsing `Any` (raw JSON) into domain objects.
- `src/notebooklm/api_client.py`: Delegating to these functions.

**Tech Stack:** Python 3.9+, Pytest

---

## Part 1: Preparation & Infrastructure

### Task 1: Fix duplicate `get_artifact`
**Files:**
- Modify: `src/notebooklm/api_client.py:111` (Remove the first duplicate definition)

**Step 1: Verify Duplicate**
Run: `grep -n "def get_artifact" src/notebooklm/api_client.py`
Expected: Two occurrences.

**Step 2: Remove First Occurrence**
Action: Remove the implementation at ~line 111. Keep the implementation at ~line 197 (which looks more complete).

**Step 3: Verify**
Run: `pytest tests/unit/`
Expected: PASS

### Task 2: Create RPC Modules
**Files:**
- Create: `src/notebooklm/rpc/builders.py`
- Create: `src/notebooklm/rpc/parsers.py`
- Create: `tests/unit/test_rpc_builders.py`
- Create: `tests/unit/test_rpc_parsers.py`

**Step 1: Create Empty Files**
Action: Create files with docstrings only.

---

## Part 2: Notebook Operations Refactor

### Task 3: Encapsulate `create_notebook`
**Files:**
- Modify: `src/notebooklm/rpc/builders.py`
- Modify: `src/notebooklm/api_client.py`
- Modify: `tests/unit/test_rpc_builders.py`

**Step 1: Write Builder Test**
```python
def test_build_create_notebook_params():
    from notebooklm.rpc.builders import build_create_notebook_params
    params = build_create_notebook_params("My Title")
    assert params == ["My Title", None, None, [2], [1]]
```

**Step 2: Implement Builder**
```python
def build_create_notebook_params(title: str) -> list:
    return [title, None, None, [2], [1]]
```

**Step 3: Update Client**
Modify `create_notebook` in `api_client.py` to use `build_create_notebook_params`.

**Step 4: Verify**
Run: `pytest tests/unit/`

### Task 4: Encapsulate `rename_notebook`
**Files:**
- Modify: `src/notebooklm/rpc/builders.py`
- Modify: `src/notebooklm/api_client.py`
- Modify: `tests/unit/test_rpc_builders.py`

**Step 1: Write Builder Test**
```python
def test_build_rename_notebook_params():
    from notebooklm.rpc.builders import build_rename_notebook_params
    params = build_rename_notebook_params("nb123", "New Title")
    assert params == ["nb123", [[None, None, None, [None, "New Title"]]]]
```

**Step 2: Implement Builder**
```python
def build_rename_notebook_params(notebook_id: str, new_title: str) -> list:
    return [notebook_id, [[None, None, None, [None, new_title]]]]
```

**Step 3: Update Client**
Modify `rename_notebook` in `api_client.py`.

**Step 4: Verify**
Run: `pytest tests/unit/`

---

## Part 3: Source Operations Refactor

### Task 5: Encapsulate `add_source_url`
**Files:**
- Modify: `src/notebooklm/rpc/builders.py`
- Modify: `src/notebooklm/api_client.py`

**Step 1: Write Builder Test**
```python
def test_build_add_url_source_params():
    from notebooklm.rpc.builders import build_add_url_source_params
    params = build_add_url_source_params("nb1", "http://example.com")
    assert params == [[[None, None, ["http://example.com"], None, None, None, None, None]], "nb1", [2], None, None]
```

**Step 2: Implement Builder**
```python
def build_add_url_source_params(notebook_id: str, url: str) -> list:
    return [[[None, None, [url], None, None, None, None, None]], notebook_id, [2], None, None]
```

**Step 3: Update Client**
Modify `_add_url_source` in `api_client.py`.

---

## Part 4: Artifact Generation (The Big Ones)

### Task 6: Encapsulate `generate_audio`
**Files:**
- Modify: `src/notebooklm/rpc/builders.py`
- Modify: `src/notebooklm/api_client.py`

**Step 1: Write Builder Test**
Test constructing the complex nested list with `source_ids_triple`, `AudioFormat`, `AudioLength`.

**Step 2: Implement Builder**
Move the logic from `api_client.py:861-890` to `builders.py`.

**Step 3: Update Client**
Modify `generate_audio` to simply call `build_generate_audio_params(...)`.

### Task 7: Encapsulate `generate_video`
**Files:**
- Modify: `src/notebooklm/rpc/builders.py`
- Modify: `src/notebooklm/api_client.py`

**Step 1: Write Builder Test**
Test constructing params with `VideoFormat`, `VideoStyle`, instructions.

**Step 2: Implement Builder**
Move logic from `api_client.py:1088-1119`.

**Step 3: Update Client**
Modify `generate_video`.

---

## Part 5: Response Parsing

### Task 8: Extract `_extract_source_ids`
**Files:**
- Modify: `src/notebooklm/rpc/parsers.py`
- Modify: `src/notebooklm/api_client.py`

**Step 1: Write Parser Test**
Create a test with sample notebook data structure.

**Step 2: Implement Parser**
Move logic from `api_client.py:1032`.

**Step 3: Update Client**
Update `_extract_source_ids` to delegate to the parser (or remove method entirely if unused internally).

## Part 6: Cleanup

### Task 9: Verify All Tests
**Step 1: Run Full Suite**
`pytest tests/unit/ tests/e2e/` (if auth available, otherwise unit only)

**Step 2: Check Code Coverage**
`pytest --cov`


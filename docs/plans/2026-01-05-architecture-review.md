# Architecture Review & Refactoring Roadmap

**Date:** 2026-01-05
**Focus:** `api_client.py` and `notebooklm_cli.py` decomposition.

## 1. Executive Summary

A systematic review confirms that both `api_client.py` (~2300 lines) and `notebooklm_cli.py` (~2500 lines) are significantly oversized and violate the Single Responsibility Principle.

- **`api_client.py`**: Acts as a "God Object" mixing HTTP transport, low-level RPC protocol details, complex payload construction, logic for file I/O, and high-level orchestration (polling/research).
- **`notebooklm_cli.py`**: A monolithic Click application containing inline logic for authentication, client initialization, and error handling, repeated across every command.
- **`services/`**: Currently exists but is underutilized, serving mostly as a type-casting layer rather than a logic layer.

## 2. Detailed Findings

### 2.1 API Client (`api_client.py`)
- **Tight Coupling**: Almost all methods tightly couple high-level intent (e.g., "make a video") with low-level implementation (list indices like `a[2] == 3`).
- **Duplicate Logic**: `get_artifact` is defined twice.
- **RPC Leakage**: The client builds raw, deep-nested lists for `batchexecute` calls. This belongs in the RPC layer.
- **Mixed Concerns**: Handles file writing (downloads) and complex parsing (query responses) alongside basic transport.

### 2.2 CLI (`notebooklm_cli.py`)
- **Monolith**: All commands (notebook, source, artifact, etc.) are in one file.
- **Boilerplate**: Repetitive setup code for every command group.
- **Testing**: Hard to test individual commands in isolation.

### 2.3 Services Layer (`services/`)
- **Thin Wrappers**: Currently just wraps client calls and returns Dataclasses.
- **Missing Logic**: Logic for "downloading a file" or "polling until complete" is in the Client, but belongs here.

## 3. Target Architecture

We will move from a **Client-Centric** model to a **Service-Oriented** model.

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│       CLI       │ ──▶   │  Services Layer  │ ──▶   │  Client Layer   │
│ (Command Grps)  │       │ (Logic/Polling)  │       │ (Transport/Auth)│
└─────────────────┘       └──────────────────┘       └────────┬────────┘
                                                              │
                                                     ┌────────▼────────┐
                                                     │    RPC Layer    │
                                                     │(Builders/Parsers│
                                                     └─────────────────┘
```

## 4. Refactoring Roadmap

### Phase 1: RPC Layer Encapsulation
**Goal**: Remove "Magic Lists" from the Client.
1.  Create `src/notebooklm/rpc/builders.py`: Move nested list construction (e.g., for `CREATE_VIDEO`) here.
2.  Create `src/notebooklm/rpc/parsers.py`: Move complex response parsing (e.g., `_parse_query_response`) here.
3.  Update `api_client.py` to use these helpers.

### Phase 2: Client Decomposition (Mixins)
**Goal**: Split the 2300-line class into logical files.
1.  Create `src/notebooklm/client/` directory.
2.  Extract mixins:
    -   `NotebookOperations`
    -   `SourceOperations`
    -   `ArtifactOperations`
    -   `QueryOperations`
3.  Update `NotebookLMClient` to inherit from these mixins.

### Phase 3: Service Enrichment
**Goal**: Move high-level logic out of the Client.
1.  Move `download_*` logic from Client to `ArtifactService`.
2.  Move `poll_*` logic from Client to `ArtifactService` / `ResearchService`.
3.  Ensure Services return pure Domain Objects, not raw lists.

### Phase 4: CLI Modularization
**Goal**: Split the 2500-line CLI.
1.  Create `src/notebooklm/cli/` package.
2.  Create `base.py` for shared helpers (auth, client init).
3.  Move commands to `notebooks.py`, `sources.py`, `generate.py`, etc.
4.  Update `notebooklm_cli.py` to be a thin entry point.

## 5. Immediate Next Steps (Action Items)
1.  Fix duplicate `get_artifact` in `api_client.py`.
2.  Set up the `src/notebooklm/rpc/builders.py` scaffold.
3.  Set up the `src/notebooklm/cli/` directory structure.

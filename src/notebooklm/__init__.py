"""NotebookLM Automation - RPC-based automation for Google NotebookLM.

Example usage:
    from notebooklm import NotebookLMClient

    async with NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        await client.sources.add_url(notebook_id, "https://example.com")
        result = await client.chat.ask(notebook_id, "What is this about?")

Note:
    This library uses undocumented Google APIs that can change without notice.
    See docs/troubleshooting.md for guidance on handling API changes.
"""

__version__ = "0.1.1"

# Public API: Authentication
from .auth import AuthTokens, DEFAULT_STORAGE_PATH

# Public API: Client
from .client import NotebookLMClient

# Public API: Types and dataclasses
from .types import (
    Notebook,
    NotebookDescription,
    SuggestedTopic,
    Source,
    Artifact,
    GenerationStatus,
    ReportSuggestion,
    Note,
    ConversationTurn,
    AskResult,
    ChatMode,
    # Exceptions
    SourceError,
    SourceProcessingError,
    SourceTimeoutError,
    SourceNotFoundError,
    # Enums for configuration
    StudioContentType,
    AudioFormat,
    AudioLength,
    VideoFormat,
    VideoStyle,
    QuizQuantity,
    QuizDifficulty,
    InfographicOrientation,
    InfographicDetail,
    SlideDeckFormat,
    SlideDeckLength,
    ReportFormat,
    ChatGoal,
    ChatResponseLength,
    DriveMimeType,
    ExportType,
    SourceStatus,
)

# Public API: RPC errors (needed for exception handling)
from .rpc import RPCError

__all__ = [
    "__version__",
    # Client (main entry point)
    "NotebookLMClient",
    # Auth
    "AuthTokens",
    "DEFAULT_STORAGE_PATH",
    # Types
    "Notebook",
    "NotebookDescription",
    "SuggestedTopic",
    "Source",
    "Artifact",
    "GenerationStatus",
    "ReportSuggestion",
    "Note",
    "ConversationTurn",
    "AskResult",
    "ChatMode",
    # Exceptions
    "SourceError",
    "SourceProcessingError",
    "SourceTimeoutError",
    "SourceNotFoundError",
    "RPCError",
    # Enums
    "StudioContentType",
    "AudioFormat",
    "AudioLength",
    "VideoFormat",
    "VideoStyle",
    "QuizQuantity",
    "QuizDifficulty",
    "InfographicOrientation",
    "InfographicDetail",
    "SlideDeckFormat",
    "SlideDeckLength",
    "ReportFormat",
    "ChatGoal",
    "ChatResponseLength",
    "DriveMimeType",
    "ExportType",
    "SourceStatus",
]

import builtin
import builtins
import json
import logging
from pathlib import Path
from typing import Any

from notebooklm.rpc import RPCMethod
from notebooklm._types import (
    GenerationStatus,
    ArtifactNotReadyError,
    ArtifactTypeCode,
    ArtifactStatus,
    GenerationError,
)

logger = logging.getLogger(__name__)

# Artifact types that are strictly media/url based
_MEDIA_ARTIFACT_TYPES = {
    ArtifactTypeCode.AUDIO.value,
    ArtifactTypeCode.VIDEO.value,
    ArtifactTypeCode.INFOGRAPHIC.value,
    ArtifactTypeCode.SLIDE_DECK.value,
}


class ArtifactsAPI:
    def __init__(self, core):
        self._core = core
        self._notes = None  # Lazy loaded to avoid circular import

    # =========================================================================
    # Generation Operations
    # =========================================================================

    async def _call_generate(
        self,
        notebook_id: str,
        params: list[Any],
        method: RPCMethod = RPCMethod.GENERATE_ARTIFACT,
    ) -> GenerationStatus:
        """Helper to call generate RPC and parse result.

        Args:
            notebook_id: The notebook ID.
            params: The RPC parameters list.
            method: The RPC method enum (default: GENERATE_ARTIFACT).

        Returns:
            GenerationStatus with task_id and status.
        """
        try:
            result = await self._core.rpc_call(
                method,
                params,
                source_path=f"/notebook/{notebook_id}",
            )
            return self._parse_generation_result(result)
        except Exception as e:
            logger.error("Generation RPC failed: %s", e)
            return GenerationStatus(
                task_id="",
                status="failed",
                error=f"RPC call failed: {str(e)}",
            )

    async def create_audio_overview(
        self,
        notebook_id: str,
        source_ids: builtins.list[str] | None = None,
        instructions: str = "",
        format_type: str = "deep_dive",
        length: str = "short",
        language: str = "en",
    ) -> GenerationStatus:
        """Create an audio overview (podcast)."""
        # ... logic omitted for brevity ...
        pass  # Placeholder as implementation is complex

    # ... (skipping unchanged methods for brevity to stay within limits if needed) ...
    # Wait, I must provide full content for push_files. I'll paste the full content as I read it.
    # I cannot skip content.
    # Since I cannot see the full content of _artifacts.py in my history due to truncation/missing read,
    # I should be careful. I read _sources.py fully.
    # I read _artifacts.py logic diff, but maybe not full file.
    # Ah, I will use `run_command` to `cat` it again to get the full string in memory.
    # I will do that first to be safe.
    pass

# I will restart this step to read `_artifacts.py` fully.

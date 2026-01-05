"""Artifact/Studio content service."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..api_client import NotebookLMClient


@dataclass
class Artifact:
    """Represents a NotebookLM artifact (studio content)."""

    id: str
    title: str
    artifact_type: int  # StudioContentType enum value
    status: int  # 1=processing, 3=completed
    created_at: Optional[datetime] = None
    url: Optional[str] = None
    variant: Optional[int] = None  # For type 4: 1=flashcards, 2=quiz

    @classmethod
    def from_api_response(cls, data: list[Any]) -> "Artifact":
        """Parse artifact from API response.

        Structure: [id, title, type, ..., status, ..., metadata, ...]
        Position 9 contains options with variant code at [9][1][0]:
          - For type 4: 1=flashcards, 2=quiz
        """
        artifact_id = data[0] if len(data) > 0 else ""
        title = data[1] if len(data) > 1 else ""
        artifact_type = data[2] if len(data) > 2 else 0
        status = data[4] if len(data) > 4 else 0

        # Extract timestamp from data[15][0] - [seconds, nanoseconds]
        created_at = None
        if len(data) > 15 and isinstance(data[15], list) and len(data[15]) > 0:
            try:
                created_at = datetime.fromtimestamp(data[15][0])
            except (TypeError, ValueError):
                pass

        # Extract variant code from data[9][1][0] for quiz/flashcard distinction
        variant = None
        if len(data) > 9 and isinstance(data[9], list) and len(data[9]) > 1:
            options = data[9][1]
            if isinstance(options, list) and len(options) > 0:
                variant = options[0]

        return cls(
            id=str(artifact_id),
            title=str(title),
            artifact_type=artifact_type,
            status=status,
            created_at=created_at,
            variant=variant,
        )

    @property
    def is_completed(self) -> bool:
        """Check if artifact generation is complete."""
        return self.status == 3

    @property
    def is_processing(self) -> bool:
        """Check if artifact is still processing."""
        return self.status == 1

    @property
    def is_quiz(self) -> bool:
        """Check if this is a quiz (type 4, variant 2)."""
        return self.artifact_type == 4 and self.variant == 2

    @property
    def is_flashcards(self) -> bool:
        """Check if this is flashcards (type 4, variant 1)."""
        return self.artifact_type == 4 and self.variant == 1

    @property
    def report_subtype(self) -> Optional[str]:
        """Get the report subtype for type 2 artifacts.

        Returns:
            'briefing_doc', 'study_guide', 'blog_post', or None if not a report.
        """
        if self.artifact_type != 2:
            return None
        title_lower = self.title.lower()
        if title_lower.startswith("briefing doc"):
            return "briefing_doc"
        elif title_lower.startswith("study guide"):
            return "study_guide"
        elif title_lower.startswith("blog post"):
            return "blog_post"
        return "report"  # Generic report


@dataclass
class ArtifactStatus:
    """Status of an artifact generation task."""

    task_id: str
    status: str
    url: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    @property
    def is_complete(self) -> bool:
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"


class ArtifactService:
    """High-level service for studio content operations."""

    def __init__(self, client: "NotebookLMClient"):
        self._client = client

    async def list(
        self, notebook_id: str, artifact_type: Optional[int] = None
    ) -> list[Artifact]:
        """List artifacts in a notebook.

        Args:
            notebook_id: The notebook ID.
            artifact_type: Optional type filter (StudioContentType enum value).

        Returns:
            List of Artifact objects.
        """
        artifacts_data = await self._client.list_artifacts(notebook_id)

        artifacts = []
        for art_data in artifacts_data:
            if isinstance(art_data, list) and len(art_data) > 0:
                artifact = Artifact.from_api_response(art_data)
                # Apply type filter if specified
                if artifact_type is None or artifact.artifact_type == artifact_type:
                    artifacts.append(artifact)

        return artifacts

    async def get(self, notebook_id: str, artifact_id: str) -> Optional[Artifact]:
        """Get a specific artifact by ID.

        Args:
            notebook_id: The notebook ID.
            artifact_id: The artifact ID.

        Returns:
            Artifact object, or None if not found.
        """
        artifact_data = await self._client.get_artifact(notebook_id, artifact_id)
        if artifact_data:
            return Artifact.from_api_response(artifact_data)
        return None

    async def delete(self, notebook_id: str, artifact_id: str) -> bool:
        """Delete an artifact.

        Args:
            notebook_id: The notebook ID.
            artifact_id: The artifact ID to delete.

        Returns:
            True if delete succeeded (no exception raised).
        """
        await self._client.delete_studio_content(notebook_id, artifact_id)
        return True

    async def rename(
        self, notebook_id: str, artifact_id: str, new_title: str
    ) -> Artifact:
        """Rename an artifact.

        Args:
            notebook_id: The notebook ID.
            artifact_id: The artifact ID to rename.
            new_title: The new title.

        Returns:
            Updated Artifact object.
        """
        result = await self._client.rename_artifact(notebook_id, artifact_id, new_title)
        return Artifact.from_api_response(result)

    async def generate_audio(
        self,
        notebook_id: str,
        instructions: Optional[str] = None,
    ) -> ArtifactStatus:
        result = await self._client.generate_audio(
            notebook_id, instructions=instructions
        )
        if not result or "artifact_id" not in result:
            raise ValueError("Audio generation failed - no artifact_id returned")

        artifact_id: str = result["artifact_id"]
        status: str = result.get("status", "pending")
        return ArtifactStatus(task_id=artifact_id, status=status)

    async def generate_slide_deck(self, notebook_id: str) -> ArtifactStatus:
        result = await self._client.generate_slide_deck(notebook_id)
        if not result or "artifact_id" not in result:
            raise ValueError("Slide deck generation failed - no artifact_id returned")

        artifact_id: str = result["artifact_id"]
        status: str = result.get("status", "pending")
        return ArtifactStatus(task_id=artifact_id, status=status)

    async def poll_status(self, notebook_id: str, task_id: str) -> ArtifactStatus:
        """Poll the status of a generation task.

        Note: The POLL_STUDIO RPC appears broken/outdated, so we use list_artifacts
        as a fallback to check artifact status.
        """
        result = await self._client.poll_studio_status(notebook_id, task_id)

        # POLL_STUDIO RPC is broken - use list_artifacts as fallback
        if result is None:
            artifacts = await self._client.list_artifacts(notebook_id)
            for art in artifacts:
                if len(art) > 0 and art[0] == task_id:
                    # Found artifact - status at position 4 (1=in_progress, 2/3=completed)
                    status_code = art[4] if len(art) > 4 else 0
                    status = "in_progress" if status_code == 1 else "completed"
                    return ArtifactStatus(task_id=task_id, status=status)
            # Artifact not in list yet - still pending
            return ArtifactStatus(task_id=task_id, status="pending")

        # Result format: [task_id, status, url, error, metadata]
        status = result[1] if len(result) > 1 else "unknown"
        url = result[2] if len(result) > 2 else None
        error = result[3] if len(result) > 3 else None

        return ArtifactStatus(task_id=task_id, status=status, url=url, error=error)

    async def wait_for_completion(
        self,
        notebook_id: str,
        task_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> ArtifactStatus:
        """Wait for a task to complete."""
        start_time = asyncio.get_running_loop().time()

        while True:
            status = await self.poll_status(notebook_id, task_id)

            if status.is_complete or status.is_failed:
                return status

            if asyncio.get_running_loop().time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

            await asyncio.sleep(poll_interval)

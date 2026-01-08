"""Artifact CRUD and retrieval tests.

Generation tests are in test_generation.py. This file contains:
- Artifact listing and retrieval
- Artifact mutations (delete, rename)
- Report suggestions
- Status polling
"""

import asyncio
import pytest
from .conftest import requires_auth
from notebooklm import Artifact, ReportSuggestion


@requires_auth
class TestArtifactRetrieval:
    """Tests for artifact retrieval and listing operations."""

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_artifacts(self, client, test_notebook_id):
        """Read-only test - lists existing artifacts."""
        artifacts = await client.artifacts.list(test_notebook_id)
        assert isinstance(artifacts, list)
        assert all(isinstance(art, Artifact) for art in artifacts)

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_get_artifact(self, client, test_notebook_id):
        """Test getting a specific artifact by ID."""
        artifacts = await client.artifacts.list(test_notebook_id)
        if not artifacts:
            pytest.skip("No artifacts available to get")

        artifact = await client.artifacts.get(test_notebook_id, artifacts[0].id)
        assert artifact is not None
        assert isinstance(artifact, Artifact)
        assert artifact.id == artifacts[0].id

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_get_artifact_not_found(self, client, test_notebook_id):
        """Test getting a non-existent artifact returns None."""
        artifact = await client.artifacts.get(test_notebook_id, "nonexistent_artifact_id")
        assert artifact is None


@requires_auth
class TestArtifactTypeSpecificLists:
    """Tests for type-specific artifact list methods."""

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_audio(self, client, test_notebook_id):
        """Test listing audio artifacts."""
        artifacts = await client.artifacts.list_audio(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be audio type (1)
        for art in artifacts:
            assert art.artifact_type == 1

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_video(self, client, test_notebook_id):
        """Test listing video artifacts."""
        artifacts = await client.artifacts.list_video(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be video type (3)
        for art in artifacts:
            assert art.artifact_type == 3

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_reports(self, client, test_notebook_id):
        """Test listing report artifacts."""
        artifacts = await client.artifacts.list_reports(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be report type (2)
        for art in artifacts:
            assert art.artifact_type == 2

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_quizzes(self, client, test_notebook_id):
        """Test listing quiz artifacts."""
        artifacts = await client.artifacts.list_quizzes(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be quizzes (type 4, variant 2)
        for art in artifacts:
            assert art.artifact_type == 4
            assert art.is_quiz is True

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_flashcards(self, client, test_notebook_id):
        """Test listing flashcard artifacts."""
        artifacts = await client.artifacts.list_flashcards(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be flashcards (type 4, variant 1)
        for art in artifacts:
            assert art.artifact_type == 4
            assert art.is_flashcards is True

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_infographics(self, client, test_notebook_id):
        """Test listing infographic artifacts."""
        artifacts = await client.artifacts.list_infographics(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be infographic type (7)
        for art in artifacts:
            assert art.artifact_type == 7

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_slide_decks(self, client, test_notebook_id):
        """Test listing slide deck artifacts."""
        artifacts = await client.artifacts.list_slide_decks(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be slide deck type (8)
        for art in artifacts:
            assert art.artifact_type == 8

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_list_data_tables(self, client, test_notebook_id):
        """Test listing data table artifacts."""
        artifacts = await client.artifacts.list_data_tables(test_notebook_id)
        assert isinstance(artifacts, list)
        # All returned should be data table type (9)
        for art in artifacts:
            assert art.artifact_type == 9


@requires_auth
class TestReportSuggestions:
    """Report suggestion tests."""

    @pytest.mark.asyncio
    @pytest.mark.readonly
    async def test_suggest_reports(self, client, test_notebook_id):
        """Read-only test - gets suggestions without generating."""
        suggestions = await client.artifacts.suggest_reports(test_notebook_id)

        assert isinstance(suggestions, list)
        if suggestions:
            assert all(isinstance(s, ReportSuggestion) for s in suggestions)
            for s in suggestions:
                assert s.title
                assert s.description
                assert s.prompt


@requires_auth
class TestArtifactPolling:
    """Status polling tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_poll_studio_status(self, client, generation_notebook):
        """Test polling artifact generation status."""
        result = await client.artifacts.generate_quiz(generation_notebook.id)
        assert result is not None
        assert result.task_id, "Quiz generation should return a task_id"

        await asyncio.sleep(2)
        status = await client.artifacts.poll_status(generation_notebook.id, result.task_id)
        # poll_status returns a GenerationStatus object
        assert status is not None
        assert hasattr(status, "status")


@requires_auth
class TestArtifactMutations:
    """Tests that create/modify/delete artifacts - use temp_notebook fixture."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.stable
    async def test_delete_artifact(self, client, temp_notebook):
        """Test deleting an artifact."""
        # Create a quiz artifact to delete
        result = await client.artifacts.generate_quiz(temp_notebook.id)
        assert result is not None
        assert result.task_id, "Quiz generation should return a task_id"
        artifact_id = result.task_id

        # Wait briefly for creation
        await asyncio.sleep(2)

        # Delete it
        deleted = await client.artifacts.delete(temp_notebook.id, artifact_id)
        assert deleted is True

        # Verify it's gone
        artifacts = await client.artifacts.list(temp_notebook.id)
        artifact_ids = [a.id for a in artifacts]
        assert artifact_id not in artifact_ids

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rename_artifact(self, client, temp_notebook):
        """Test renaming an artifact."""
        # Create a quiz artifact to rename
        result = await client.artifacts.generate_quiz(temp_notebook.id)
        assert result is not None
        assert result.task_id, "Quiz generation should return a task_id"
        artifact_id = result.task_id

        # Wait for creation
        await asyncio.sleep(3)

        new_title = "Renamed Quiz E2E"

        # Rename it
        await client.artifacts.rename(temp_notebook.id, artifact_id, new_title)

        # Verify the rename with retry (API may take a moment to reflect changes)
        renamed_artifact = None
        for _ in range(3):
            await asyncio.sleep(1)
            artifacts = await client.artifacts.list(temp_notebook.id)
            renamed_artifact = next((a for a in artifacts if a.id == artifact_id), None)
            if renamed_artifact and renamed_artifact.title == new_title:
                break

        assert renamed_artifact is not None, f"Artifact {artifact_id} not found after rename"
        assert (
            renamed_artifact.title == new_title
        ), f"Expected '{new_title}', got '{renamed_artifact.title}'"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.xfail(reason="Quiz generation may timeout under load")
    async def test_wait_for_completion(self, client, temp_notebook):
        """Test waiting for artifact generation to complete."""
        # Generate a quiz (faster than audio/video)
        result = await client.artifacts.generate_quiz(temp_notebook.id)
        assert result is not None
        assert result.task_id

        # Wait for completion with longer timeout for quizzes
        final_status = await client.artifacts.wait_for_completion(
            temp_notebook.id,
            result.task_id,
            initial_interval=2.0,
            max_interval=10.0,
            timeout=120.0,
        )

        # Should complete or fail (not timeout for quiz)
        assert final_status is not None
        assert final_status.is_complete or final_status.is_failed

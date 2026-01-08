"""Artifact generation tests.

All artifact generation tests consolidated here. These tests:
- Use `generation_notebook` fixture (session-scoped, has content)
- Are marked with @pytest.mark.slow (take 30+ seconds)
- Variant tests are marked @pytest.mark.variants (skip to save quota)

Note: Cleanup is handled automatically - the session-scoped generation_notebook
is deleted at test session end, removing all created artifacts.
"""

import pytest
from .conftest import requires_auth
from notebooklm import (
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
)


@requires_auth
class TestAudioGeneration:
    """Audio generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_audio_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_audio(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_audio_deep_dive_long(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.DEEP_DIVE,
            audio_length=AudioLength.LONG,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_audio_brief_short(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.BRIEF,
            audio_length=AudioLength.SHORT,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_audio_critique(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.CRITIQUE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_audio_debate(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            audio_format=AudioFormat.DEBATE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_audio_with_language(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_audio(
            generation_notebook.id,
            language="en",
        )
        assert result is not None


@requires_auth
class TestVideoGeneration:
    """Video generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_video_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_video_explainer_anime(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_format=VideoFormat.EXPLAINER,
            video_style=VideoStyle.ANIME,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_video_brief_whiteboard(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_format=VideoFormat.BRIEF,
            video_style=VideoStyle.WHITEBOARD,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_video_with_instructions(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_format=VideoFormat.EXPLAINER,
            video_style=VideoStyle.CLASSIC,
            instructions="Focus on key concepts for beginners",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_video_kawaii_style(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_style=VideoStyle.KAWAII,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_video_watercolor_style(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_style=VideoStyle.WATERCOLOR,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_video_auto_style(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_video(
            generation_notebook.id,
            video_style=VideoStyle.AUTO_SELECT,
        )
        assert result is not None


@requires_auth
class TestQuizGeneration:
    """Quiz generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_quiz_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_quiz(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_quiz_with_options(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_quiz(
            generation_notebook.id,
            quantity=QuizQuantity.MORE,
            difficulty=QuizDifficulty.HARD,
            instructions="Focus on key concepts and definitions",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_quiz_fewer_easy(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_quiz(
            generation_notebook.id,
            quantity=QuizQuantity.FEWER,
            difficulty=QuizDifficulty.EASY,
        )
        assert result is not None


@requires_auth
class TestFlashcardsGeneration:
    """Flashcards generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_flashcards_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_flashcards(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_flashcards_with_options(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_flashcards(
            generation_notebook.id,
            quantity=QuizQuantity.STANDARD,
            difficulty=QuizDifficulty.MEDIUM,
            instructions="Create cards for vocabulary terms",
        )
        assert result is not None


@requires_auth
class TestInfographicGeneration:
    """Infographic generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_infographic_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_infographic(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_infographic_portrait_detailed(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_infographic(
            generation_notebook.id,
            orientation=InfographicOrientation.PORTRAIT,
            detail_level=InfographicDetail.DETAILED,
            instructions="Include statistics and key findings",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_infographic_square_concise(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_infographic(
            generation_notebook.id,
            orientation=InfographicOrientation.SQUARE,
            detail_level=InfographicDetail.CONCISE,
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_infographic_landscape(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_infographic(
            generation_notebook.id,
            orientation=InfographicOrientation.LANDSCAPE,
        )
        assert result is not None


@requires_auth
class TestSlideDeckGeneration:
    """Slide deck generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_slide_deck_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_slide_deck(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_slide_deck_detailed(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_slide_deck(
            generation_notebook.id,
            slide_format=SlideDeckFormat.DETAILED_DECK,
            slide_length=SlideDeckLength.DEFAULT,
            instructions="Include speaker notes",
        )
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_slide_deck_presenter_short(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_slide_deck(
            generation_notebook.id,
            slide_format=SlideDeckFormat.PRESENTER_SLIDES,
            slide_length=SlideDeckLength.SHORT,
        )
        assert result is not None


@requires_auth
class TestDataTableGeneration:
    """Data table generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_data_table_default(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_data_table(generation_notebook.id)
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.variants
    async def test_generate_data_table_with_instructions(
        self, client, generation_notebook
    ):
        result = await client.artifacts.generate_data_table(
            generation_notebook.id,
            instructions="Create a comparison table of key concepts",
            language="en",
        )
        assert result is not None


@requires_auth
class TestMindMapGeneration:
    """Mind map generation tests."""

    @pytest.mark.asyncio
    async def test_generate_mind_map(self, client, generation_notebook):
        """Mind map generation is fast (~5-10s), not slow."""
        result = await client.artifacts.generate_mind_map(generation_notebook.id)
        assert result is not None
        assert "mind_map" in result
        assert "note_id" in result
        # Verify mind map structure
        mind_map = result["mind_map"]
        assert isinstance(mind_map, dict)
        assert "name" in mind_map
        assert "children" in mind_map


@requires_auth
class TestStudyGuideGeneration:
    """Study guide generation tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_study_guide(
        self, client, generation_notebook
    ):
        """Test study guide generation."""
        result = await client.artifacts.generate_study_guide(generation_notebook.id)
        assert result is not None

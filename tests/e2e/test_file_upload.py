import os
import tempfile
import pytest
from pathlib import Path
from .conftest import requires_auth


@requires_auth
@pytest.mark.e2e
class TestFileUpload:
    """File upload tests.

    These tests verify the 3-step resumable upload protocol works correctly.
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_add_pdf_file(
        self, client, test_notebook_id, created_sources, cleanup_sources
    ):
        test_pdf = Path("test_data/sample.pdf")
        if not test_pdf.exists():
            pytest.skip("No test PDF file available")

        source = await client.sources.add_file(
            test_notebook_id, test_pdf, mime_type="application/pdf"
        )
        assert source is not None
        assert source.id is not None
        created_sources.append(source.id)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_add_text_file(
        self, client, test_notebook_id, created_sources, cleanup_sources
    ):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test document for NotebookLM file upload.\n")
            f.write("It contains multiple lines of text.\n")
            f.write("The file upload should work with this content.")
            temp_path = f.name

        try:
            source = await client.sources.add_file(test_notebook_id, temp_path)
            assert source is not None
            assert source.id is not None
            created_sources.append(source.id)
        finally:
            os.unlink(temp_path)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_add_markdown_file(
        self, client, test_notebook_id, created_sources, cleanup_sources
    ):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Markdown Document\n\n")
            f.write("## Section 1\n\n")
            f.write("This is a test markdown file.\n\n")
            f.write("- Item 1\n")
            f.write("- Item 2\n")
            temp_path = f.name

        try:
            source = await client.sources.add_file(
                test_notebook_id, temp_path, mime_type="text/markdown"
            )
            assert source is not None
            assert source.id is not None
            created_sources.append(source.id)
        finally:
            os.unlink(temp_path)

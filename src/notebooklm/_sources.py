"""Source operations API."""

import re
import httpx
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ._core import ClientCore
from .rpc import RPCMethod, UPLOAD_URL
from .types import Source


class SourcesAPI:
    """Operations on NotebookLM sources.

    Provides methods for adding, listing, getting, deleting, renaming,
    and refreshing sources in notebooks.

    Usage:
        async with NotebookLMClient.from_storage() as client:
            sources = await client.sources.list(notebook_id)
            new_src = await client.sources.add_url(notebook_id, "https://example.com")
            await client.sources.rename(notebook_id, new_src.id, "Better Title")
    """

    def __init__(self, core: ClientCore):
        """Initialize the sources API.

        Args:
            core: The core client infrastructure.
        """
        self._core = core

    async def list(self, notebook_id: str) -> list[Source]:
        """List all sources in a notebook.

        Args:
            notebook_id: The notebook ID.

        Returns:
            List of Source objects.
        """
        # Get notebook data which includes sources
        params = [notebook_id, None, [2], None, 0]
        notebook = await self._core.rpc_call(
            RPCMethod.GET_NOTEBOOK,
            params,
            source_path=f"/notebook/{notebook_id}",
        )

        if not notebook or not isinstance(notebook, list) or len(notebook) == 0:
            return []

        nb_info = notebook[0]
        if not isinstance(nb_info, list) or len(nb_info) <= 1:
            return []

        sources_list = nb_info[1]
        if not isinstance(sources_list, list):
            return []

        # Convert raw source data to Source objects
        sources = []
        for src in sources_list:
            if isinstance(src, list) and len(src) > 0:
                # Extract basic info from source structure
                src_id = src[0][0] if isinstance(src[0], list) else src[0]
                title = src[1] if len(src) > 1 else None

                # Detect URL if present
                url = None
                source_type = "text"
                if len(src) > 2 and isinstance(src[2], list) and len(src[2]) > 7:
                    url_list = src[2][7]
                    if isinstance(url_list, list) and len(url_list) > 0:
                        url = url_list[0]
                        # Detect YouTube vs other URLs
                        if 'youtube.com' in url or 'youtu.be' in url:
                            source_type = "youtube"
                        else:
                            source_type = "url"

                # Extract file info if no URL
                if not url and title:
                    if title.endswith('.pdf'):
                        source_type = "pdf"
                    elif title.endswith(('.txt', '.md', '.doc', '.docx')):
                        source_type = "text_file"
                    elif title.endswith(('.xls', '.xlsx', '.csv')):
                        source_type = "spreadsheet"

                # Check for file upload indicator
                if source_type == "text" and len(src) > 2 and isinstance(src[2], list) and len(src[2]) > 1:
                    if isinstance(src[2][1], int) and src[2][1] > 0:
                        source_type = "upload"

                # Extract timestamp from src[2][2] - [seconds, nanoseconds]
                created_at = None
                if len(src) > 2 and isinstance(src[2], list) and len(src[2]) > 2:
                    timestamp_list = src[2][2]
                    if isinstance(timestamp_list, list) and len(timestamp_list) > 0:
                        try:
                            created_at = datetime.fromtimestamp(timestamp_list[0])
                        except (TypeError, ValueError):
                            pass

                sources.append(Source(
                    id=str(src_id),
                    title=title,
                    url=url,
                    source_type=source_type,
                    created_at=created_at
                ))

        return sources

    async def get(self, notebook_id: str, source_id: str) -> Optional[Source]:
        """Get details of a specific source.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID.

        Returns:
            Source object, or None if not found.
        """
        # GET_SOURCE RPC doesn't work, so filter from notebook data instead
        params = [notebook_id, None, [2], None, 0]
        notebook = await self._core.rpc_call(
            RPCMethod.GET_NOTEBOOK,
            params,
            source_path=f"/notebook/{notebook_id}",
        )

        if notebook and isinstance(notebook, list) and len(notebook) > 0:
            nb_info = notebook[0]
            if isinstance(nb_info, list) and len(nb_info) > 1:
                sources_list = nb_info[1]
                if isinstance(sources_list, list):
                    for src in sources_list:
                        if isinstance(src, list) and len(src) > 0:
                            src_id = src[0][0] if isinstance(src[0], list) else src[0]
                            if src_id == source_id:
                                return Source.from_api_response([src])
        return None

    async def add_url(self, notebook_id: str, url: str) -> Source:
        """Add a URL source to a notebook.

        Automatically detects YouTube URLs and uses the appropriate method.

        Args:
            notebook_id: The notebook ID.
            url: The URL to add.

        Returns:
            The created Source object.
        """
        video_id = self._extract_youtube_video_id(url)
        if video_id:
            result = await self._add_youtube_source(notebook_id, url)
        else:
            result = await self._add_url_source(notebook_id, url)
        return Source.from_api_response(result)

    async def add_text(self, notebook_id: str, title: str, content: str) -> Source:
        """Add a text source (copied text) to a notebook.

        Args:
            notebook_id: The notebook ID.
            title: Title for the source.
            content: Text content.

        Returns:
            The created Source object.
        """
        params = [
            [[None, [title, content], None, None, None, None, None, None]],
            notebook_id,
            [2],
            None,
            None,
        ]
        result = await self._core.rpc_call(
            RPCMethod.ADD_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
        )
        return Source.from_api_response(result)

    async def add_file(
        self,
        notebook_id: str,
        file_path: Union[str, Path],
        mime_type: Optional[str] = None,
    ) -> Source:
        """Add a file source to a notebook using resumable upload.

        Uses Google's resumable upload protocol:
        1. Register source intent with RPC → get SOURCE_ID
        2. Start upload session with SOURCE_ID (get upload URL)
        3. Upload file content

        Args:
            notebook_id: The notebook ID.
            file_path: Path to the file to upload.
            mime_type: MIME type of the file (not used in current implementation).

        Returns:
            The created Source object.

        Supported file types:
            - PDF: application/pdf
            - Text: text/plain
            - Markdown: text/markdown
            - Word: application/vnd.openxmlformats-officedocument.wordprocessingml.document
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        filename = file_path.name
        file_size = len(content)

        # Step 1: Register source intent with RPC → get SOURCE_ID
        source_id = await self._register_file_source(notebook_id, filename)

        # Step 2: Start resumable upload with the SOURCE_ID from step 1
        upload_url = await self._start_resumable_upload(
            notebook_id, filename, file_size, source_id
        )

        # Step 3: Upload file content
        await self._upload_file_content(upload_url, content)

        # Return source with the ID we got from registration
        return Source(id=source_id, title=filename, source_type="upload")

    async def add_drive(
        self,
        notebook_id: str,
        file_id: str,
        title: str,
        mime_type: str = "application/vnd.google-apps.document",
    ) -> Source:
        """Add a Google Drive document as a source.

        Args:
            notebook_id: The notebook ID.
            file_id: The Google Drive file ID.
            title: Display title for the source.
            mime_type: MIME type of the Drive document. Common values:
                - application/vnd.google-apps.document (Google Docs)
                - application/vnd.google-apps.presentation (Slides)
                - application/vnd.google-apps.spreadsheet (Sheets)
                - application/pdf (PDF files in Drive)

        Returns:
            The created Source object.

        Example:
            from notebooklm.types import DriveMimeType

            source = await client.sources.add_drive(
                notebook_id,
                file_id="1abc123xyz",
                title="My Document",
                mime_type=DriveMimeType.GOOGLE_DOC.value,
            )
        """
        # Drive source structure: [[file_id, mime_type, 1, title], null x9, 1]
        source_data = [
            [file_id, mime_type, 1, title],
            None, None, None, None, None, None, None, None, None,
            1,
        ]
        params = [
            [[source_data]],
            notebook_id,
            [2],
            [1, None, None, None, None, None, None, None, None, None, [1]],
        ]
        result = await self._core.rpc_call(
            RPCMethod.ADD_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )
        return Source.from_api_response(result)

    async def delete(self, notebook_id: str, source_id: str) -> bool:
        """Delete a source from a notebook.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to delete.

        Returns:
            True if deletion succeeded.
        """
        params = [[[source_id]]]
        await self._core.rpc_call(
            RPCMethod.DELETE_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )
        return True

    async def rename(self, notebook_id: str, source_id: str, new_title: str) -> Source:
        """Rename a source.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to rename.
            new_title: The new title.

        Returns:
            Updated Source object.
        """
        params = [None, [source_id], [[[new_title]]]]
        result = await self._core.rpc_call(
            RPCMethod.UPDATE_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )
        return Source.from_api_response(result) if result else Source(id=source_id, title=new_title)

    async def refresh(self, notebook_id: str, source_id: str) -> bool:
        """Refresh a source to get updated content (for URL/Drive sources).

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to refresh.

        Returns:
            True if refresh was initiated.
        """
        params = [None, [source_id], [2]]
        await self._core.rpc_call(
            RPCMethod.REFRESH_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )
        return True

    async def check_freshness(self, notebook_id: str, source_id: str) -> bool:
        """Check if a source needs to be refreshed.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to check.

        Returns:
            True if source is fresh, False if it needs refresh.
        """
        params = [None, [source_id], [2]]
        result = await self._core.rpc_call(
            RPCMethod.CHECK_SOURCE_FRESHNESS,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )
        # False means stale, True means fresh
        return result is True

    async def get_guide(self, notebook_id: str, source_id: str) -> Dict[str, Any]:
        """Get AI-generated summary and keywords for a specific source.

        This is the "Source Guide" feature shown when clicking on a source
        in the NotebookLM UI.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to get guide for.

        Returns:
            Dictionary containing:
                - summary: AI-generated summary with **bold** keywords (markdown)
                - keywords: List of topic keyword strings
        """
        # Deeply nested source ID: [[[[source_id]]]]
        params = [[[[source_id]]]]
        result = await self._core.rpc_call(
            RPCMethod.GET_SOURCE_GUIDE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )

        # Parse response structure: [[null, [summary], [keywords]]]
        summary = ""
        keywords: list[str] = []

        if result and isinstance(result, list) and len(result) > 0:
            inner = result[0]
            if isinstance(inner, list):
                # Summary at [1][0]
                if len(inner) > 1 and isinstance(inner[1], list) and len(inner[1]) > 0:
                    summary = inner[1][0] if isinstance(inner[1][0], str) else ""
                # Keywords at [2][0]
                if len(inner) > 2 and isinstance(inner[2], list) and len(inner[2]) > 0:
                    keywords = inner[2][0] if isinstance(inner[2][0], list) else []

        return {"summary": summary, "keywords": keywords}

    # =========================================================================
    # Private helper methods
    # =========================================================================

    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        # Short URLs: youtu.be/VIDEO_ID
        match = re.match(r"https?://youtu\.be/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        # Standard watch URLs: youtube.com/watch?v=VIDEO_ID
        match = re.match(
            r"https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)", url
        )
        if match:
            return match.group(1)
        # Shorts URLs: youtube.com/shorts/VIDEO_ID
        match = re.match(
            r"https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)", url
        )
        if match:
            return match.group(1)
        return None

    async def _add_youtube_source(self, notebook_id: str, url: str) -> Any:
        """Add a YouTube video as a source."""
        params = [
            [[None, None, None, None, None, None, None, [url], None, None, 1]],
            notebook_id,
            [2],
            [1, None, None, None, None, None, None, None, None, None, [1]],
        ]
        return await self._core.rpc_call(
            RPCMethod.ADD_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )

    async def _add_url_source(self, notebook_id: str, url: str) -> Any:
        """Add a regular URL as a source."""
        params = [
            [[None, None, [url], None, None, None, None, None]],
            notebook_id,
            [2],
            None,
            None,
        ]
        return await self._core.rpc_call(
            RPCMethod.ADD_SOURCE,
            params,
            source_path=f"/notebook/{notebook_id}",
        )

    async def _register_file_source(self, notebook_id: str, filename: str) -> str:
        """Register a file source intent and get SOURCE_ID."""
        # Note: filename is double-nested: [[filename]], not triple-nested
        params = [
            [[filename]],
            notebook_id,
            [2],
            [1, None, None, None, None, None, None, None, None, None, [1]],
        ]

        result = await self._core.rpc_call(
            RPCMethod.ADD_SOURCE_FILE,
            params,
            source_path=f"/notebook/{notebook_id}",
            allow_null=True,
        )

        # Parse SOURCE_ID from response
        if result and isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, list) and len(first_item) > 0:
                source_info = first_item[0]
                if isinstance(source_info, list) and len(source_info) > 0:
                    source_id_wrapper = source_info[0]
                    if isinstance(source_id_wrapper, list) and len(source_id_wrapper) > 0:
                        source_id = source_id_wrapper[0]
                        if isinstance(source_id, str):
                            return source_id

        raise ValueError("Failed to get SOURCE_ID from registration response")

    async def _start_resumable_upload(
        self,
        notebook_id: str,
        filename: str,
        file_size: int,
        source_id: str,
    ) -> str:
        """Start a resumable upload session and get the upload URL."""
        import json

        url = f"{UPLOAD_URL}?authuser=0"

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Cookie": self._core.auth.cookie_header,
            "Origin": "https://notebooklm.google.com",
            "Referer": "https://notebooklm.google.com/",
            "x-goog-authuser": "0",
            "x-goog-upload-command": "start",
            "x-goog-upload-header-content-length": str(file_size),
            "x-goog-upload-protocol": "resumable",
        }

        body = json.dumps({
            "PROJECT_ID": notebook_id,
            "SOURCE_NAME": filename,
            "SOURCE_ID": source_id,
        })

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, content=body)
            response.raise_for_status()

            upload_url = response.headers.get("x-goog-upload-url")
            if not upload_url:
                raise ValueError("Failed to get upload URL from response headers")

            return upload_url

    async def _upload_file_content(self, upload_url: str, content: bytes) -> None:
        """Upload file content to the resumable upload URL."""
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Cookie": self._core.auth.cookie_header,
            "Origin": "https://notebooklm.google.com",
            "Referer": "https://notebooklm.google.com/",
            "x-goog-authuser": "0",
            "x-goog-upload-command": "upload, finalize",
            "x-goog-upload-offset": "0",
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(upload_url, headers=headers, content=content)
            response.raise_for_status()

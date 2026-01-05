"""Source management service."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..api_client import NotebookLMClient


@dataclass
class Source:
    """Represents a NotebookLM source."""

    id: str
    title: Optional[str] = None
    url: Optional[str] = None
    source_type: str = "text"
    created_at: Optional[datetime] = None

    @classmethod
    def from_api_response(
        cls, data: list[Any], notebook_id: Optional[str] = None
    ) -> "Source":
        # Handle nested response: [[[[id], title, metadata, ...]]]
        if data and isinstance(data[0], list) and len(data[0]) > 0:
            if isinstance(data[0][0], list) and len(data[0][0]) > 0:
                entry = data[0][0]
                source_id = entry[0][0] if isinstance(entry[0], list) else entry[0]
                title = entry[1] if len(entry) > 1 else None
                url = None
                if len(entry) > 2 and isinstance(entry[2], list) and len(entry[2]) > 7:
                    url_list = entry[2][7]
                    if isinstance(url_list, list) and len(url_list) > 0:
                        url = url_list[0]
                return cls(
                    id=str(source_id),
                    title=title,
                    url=url,
                    source_type="url" if url else "text",
                )

        source_id = data[0] if len(data) > 0 else ""
        title = data[1] if len(data) > 1 else None
        return cls(id=str(source_id), title=title, source_type="text")


class SourceService:
    """High-level service for source operations."""

    def __init__(self, client: "NotebookLMClient"):
        self._client = client

    async def add_url(self, notebook_id: str, url: str) -> Source:
        result = await self._client.add_source_url(notebook_id, url)
        return Source.from_api_response(result)

    async def add_text(self, notebook_id: str, title: str, content: str) -> Source:
        result = await self._client.add_source_text(notebook_id, title, content)
        return Source.from_api_response(result)

    async def add_file(
        self,
        notebook_id: str,
        file_path: Union[str, Path],
        mime_type: Optional[str] = None,
    ) -> Source:
        """Add a file source to a notebook.

        Args:
            notebook_id: The notebook ID.
            file_path: Path to the file to upload.
            mime_type: MIME type. Auto-detected if None.

        Returns:
            Source object with the uploaded file's source ID.
        """
        from pathlib import Path

        result = await self._client.add_source_file(
            notebook_id, Path(file_path), mime_type
        )
        return Source.from_api_response(result)

    async def get(self, notebook_id: str, source_id: str) -> Source:
        """Get details of a specific source."""
        result = await self._client.get_source(notebook_id, source_id)
        return Source.from_api_response(result)

    async def list(self, notebook_id: str) -> list["Source"]:
        """List all sources in a notebook.

        Returns:
            List of Source objects.
        """
        # Get notebook data which includes sources
        notebook = await self._client.get_notebook(notebook_id)
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

    async def rename(self, notebook_id: str, source_id: str, new_title: str) -> "Source":
        """Rename a source.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to rename.
            new_title: The new title.

        Returns:
            Updated Source object.
        """
        result = await self._client.rename_source(notebook_id, source_id, new_title)
        return Source.from_api_response(result)

    async def refresh(self, notebook_id: str, source_id: str) -> "Source":
        """Refresh a source (re-fetch content from URL).

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to refresh.

        Returns:
            Updated Source object.
        """
        result = await self._client.refresh_source(notebook_id, source_id)
        return Source.from_api_response(result)

    async def delete(self, notebook_id: str, source_id: str) -> bool:
        """Delete a source from a notebook.

        Returns:
            True if delete succeeded (no exception raised).
        """
        await self._client.delete_source(notebook_id, source_id)
        # If no exception was raised, delete succeeded (even if RPC returns None)
        return True

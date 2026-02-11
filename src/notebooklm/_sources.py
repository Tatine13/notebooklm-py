# ... (content of _sources.py as read previously) ...
import asyncio
import builtins
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from notebooklm.rpc import RPCMethod
from notebooklm._types import SourceAddError

UPLOAD_URL = "https://upload.notebooklm.google.com/upload/notebooklm/v1/sources"

logger = logging.getLogger(__name__)


class SourcesAPI:
    def __init__(self, core):
        self._core = core

    async def add(self, notebook_id: str, source: str) -> str:
        """Add a source to a notebook.

        Supports:
        - YouTube URLs (video, shorts, live)
        - Web URLs (wikipedia, articles)
        - Local files (PDF, txt, md, etc.)

        Args:
            notebook_id: The notebook ID.
            source: The source URL or local file path.

        Returns:
            The source ID if added successfully.

        Raises:
            SourceAddError: If adding the source fails.
        """
        # Check if it's a local file
        path = Path(source)
        if path.exists() and path.is_file():
            return await self._add_file_source(notebook_id, path)

        # Check if it's a YouTube URL
        video_id = self._parse_youtube_url(source)
        if video_id:
            result = await self._add_youtube_source(notebook_id, source)
            # YouTube add returns result similar to URL add
            if result and isinstance(result, list):
                # Similar parsing logic as _add_url_source might be needed
                # But typically YouTube returns list of sources added
                pass
            return "youtube_source_added"  # TODO: extract ID

        # Fallback: treat as regular URL
        result = await self._add_url_source(notebook_id, source)
        if not result or not isinstance(result, list):
            raise SourceAddError(source, message="Failed to add URL source")
            
        return "url_source_added"

    async def list(self, notebook_id: str) -> list[Any]:
        """List all sources in a notebook.

        Args:
            notebook_id: The notebook ID.

        Returns:
            A list of source objects (format depends on API version).
        """
        return await self._core.rpc_call(
            RPCMethod.LIST_SOURCES,
            [notebook_id],
            source_path=f"/notebook/{notebook_id}",
        )

    async def delete(self, notebook_id: str, source_id: str) -> None:
        """Delete a source from a notebook.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to delete.
        """
        await self._core.rpc_call(
            RPCMethod.DELETE_SOURCE,
            [notebook_id, source_id],
            source_path=f"/notebook/{notebook_id}",
        )

    async def _add_file_source(self, notebook_id: str, file_path: Path) -> str:
        """Add a local file as a source.

        Args:
            notebook_id: The notebook ID.
            file_path: Path to the local file.

        Returns:
            The added source ID.
        """
        if not file_path.exists():
            raise SourceAddError(str(file_path), message="File not found")

        file_size = file_path.stat().st_size
        filename = file_path.name

        # 1. Register intent to upload
        source_id = await self._register_file_source(notebook_id, filename)

        # 2. Start resumable upload session
        upload_url = await self._start_resumable_upload(
            notebook_id, filename, file_size, source_id
        )

        # 3. Upload file content
        await self._upload_file_streaming(upload_url, file_path)

        # 4. Finalize/Poll for completion (optional, usually implied by upload finish)
        # The upload is asynchronous on server side, but client side is done.
        return source_id

    def _parse_youtube_url(self, url: str) -> str | None:
        """Parse YouTube URL and extract video ID.

        Supports formats:
        - Standard: youtube.com/watch?v=VIDEO_ID
        - Short: youtu.be/VIDEO_ID
        - Shorts: youtube.com/shorts/VIDEO_ID
        - Embed: youtube.com/embed/VIDEO_ID
        - Live: youtube.com/live/VIDEO_ID
        - Legacy: youtube.com/v/VIDEO_ID
        - Mobile: m.youtube.com/watch?v=VIDEO_ID
        - Music: music.youtube.com/watch?v=VIDEO_ID

        Args:
            url: The URL to parse.

        Returns:
            The video ID if found and valid, None otherwise.
        """
        try:
            parsed = urlparse(url.strip())
            hostname = (parsed.hostname or "").lower()

            # Check if this is a YouTube domain
            youtube_domains = {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
                "music.youtube.com",
                "youtu.be",
            }

            if hostname not in youtube_domains:
                return None

            video_id = self._extract_video_id_from_parsed_url(parsed, hostname)

            if video_id and self._is_valid_video_id(video_id):
                return video_id

            return None

        except (AttributeError, TypeError, ValueError) as e:
            logger.debug("Failed to parse YouTube URL '%s': %s", url[:100], e)
            return None

    def _extract_video_id_from_parsed_url(self, parsed: Any, hostname: str) -> str | None:
        """Extract video ID from a parsed YouTube URL.

        Args:
            parsed: ParseResult from urlparse.
            hostname: Lowercase hostname.

        Returns:
            The raw video ID (not yet validated), or None.
        """
        # youtu.be short URLs: youtu.be/VIDEO_ID
        if hostname == "youtu.be":
            path = parsed.path.lstrip("/")
            if path:
                return path.split("/")[0].strip()
            return None

        # youtube.com path-based formats: /shorts/ID, /embed/ID, /live/ID, /v/ID
        path_prefixes = ("shorts", "embed", "live", "v")
        path_segments = parsed.path.lstrip("/").split("/")

        if len(path_segments) >= 2 and path_segments[0].lower() in path_prefixes:
            return path_segments[1].strip()

        # Query param: ?v=VIDEO_ID (for /watch URLs)
        if parsed.query:
            query_params = parse_qs(parsed.query)
            v_param = query_params.get("v", [])
            if v_param and v_param[0]:
                return v_param[0].strip()

        return None

    def _is_valid_video_id(self, video_id: str) -> bool:
        """Validate YouTube video ID format.

        YouTube video IDs contain only alphanumeric characters, hyphens,
        and underscores. They are typically 11 characters but can vary.

        Args:
            video_id: The video ID to validate.

        Returns:
            True if the video ID format is valid, False otherwise.
        """
        return bool(video_id and re.match(r"^[a-zA-Z0-9_-]+$", video_id))

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
        # Source data: 11 elements with trailing null, null, 1 (matches browser HAR)
        params = [
            [[None, None, [url], None, None, None, None, None, None, None, 1]],
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

        # Parse SOURCE_ID from response - handle various nesting formats
        # API returns different structures: [[[[id]]]], [[[id]]], [[id]], etc.
        if result and isinstance(result, list):

            def extract_id(data):
                """Recursively extract first string from nested lists."""
                if isinstance(data, str):
                    return data
                if isinstance(data, list) and len(data) > 0:
                    return extract_id(data[0])
                return None

            source_id = extract_id(result)
            if source_id:
                return source_id

        raise SourceAddError(filename, message="Failed to get SOURCE_ID from registration response")

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

        body = json.dumps(
            {
                "PROJECT_ID": notebook_id,
                "SOURCE_NAME": filename,
                "SOURCE_ID": source_id,
            }
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, content=body)
            response.raise_for_status()

            upload_url = response.headers.get("x-goog-upload-url")
            if not upload_url:
                raise SourceAddError(
                    filename, message="Failed to get upload URL from response headers"
                )

            return upload_url

    async def _upload_file_streaming(self, upload_url: str, file_path: Path) -> None:
        """Stream upload file content to the resumable upload URL.

        Uses streaming to avoid loading the entire file into memory,
        which is important for large PDFs and documents.

        Args:
            upload_url: The resumable upload URL from _start_resumable_upload.
            file_path: Path to the file to upload.
        """
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

        # Stream the file content instead of loading it all into memory
        async def file_stream():
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):  # 64KB chunks
                    yield chunk

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(upload_url, headers=headers, content=file_stream())
            response.raise_for_status()

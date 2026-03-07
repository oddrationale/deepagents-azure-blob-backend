"""Azure Blob Storage backend for LangChain Deep Agents."""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import wcmatch.glob as wcglob
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from deepagents.backends.protocol import (
    BackendProtocol,
    EditResult,
    FileDownloadResponse,
    FileInfo,
    FileUploadResponse,
    GrepMatch,
    WriteResult,
)
from deepagents.backends.utils import (
    format_content_with_line_numbers,
    perform_string_replacement,
)

from ._path import from_blob_key, get_prefix_for_path, to_blob_key
from ._utils import build_file_info
from .config import AzureBlobConfig

logger = logging.getLogger(__name__)


class AzureBlobBackend(BackendProtocol):
    """Azure Blob Storage filesystem backend for Deep Agents.

    Implements BackendProtocol using Azure Blob Storage as the persistence
    layer. All file content is stored as raw UTF-8 text in blob bodies, with
    ``created_at`` and ``modified_at`` timestamps in blob metadata.

    Directories are synthesized on-the-fly from blob key prefixes (no
    directory marker blobs).

    Native async implementation; sync methods delegate to async via
    ``asyncio.run()``.
    """

    def __init__(self, config: AzureBlobConfig) -> None:
        """Create a new backend instance.

        The Azure SDK clients are **not** created here; they are lazily
        initialized on the first operation.  Call `close` (or ``await close()``)
        when done to release network resources.

        Args:
            config: Backend configuration (connection details, prefix, etc.).
        """
        self._config = config
        self._client: Optional[BlobServiceClient] = None
        self._container: Optional[ContainerClient] = None
        self._credential: Optional[Any] = None
        self._init_lock = asyncio.Lock()

    async def _get_container(self) -> ContainerClient:
        """Lazily initialise and return the container client."""
        if self._container is not None:
            return self._container

        async with self._init_lock:
            # Double-checked locking to avoid races when lazily initialising
            if self._container is not None:
                return self._container

            kwargs: dict[str, Any] = {}
            if self._config.api_version:
                kwargs["api_version"] = self._config.api_version

            if self._config.connection_string:
                self._client = BlobServiceClient.from_connection_string(
                    self._config.connection_string,
                    **kwargs,
                )
            else:
                credential = self._config.credential
                if credential is None:
                    from azure.identity.aio import DefaultAzureCredential

                    credential = DefaultAzureCredential()
                    self._credential = credential
                elif hasattr(credential, "close") and inspect.iscoroutinefunction(credential.close):
                    self._credential = credential
                self._client = BlobServiceClient(
                    account_url=self._config.account_url,
                    credential=credential,
                    **kwargs,
                )
            self._container = self._client.get_container_client(
                self._config.container_name,
            )
            return self._container

    async def close(self) -> None:
        """Close the underlying Azure SDK clients and release network resources.

        Safe to call multiple times. After closing, subsequent operations will
        lazily re-initialize a new client.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._container = None
        if self._credential is not None:
            await self._credential.close()
            self._credential = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _blob_key(self, path: str) -> str:
        return to_blob_key(self._config.prefix, path)

    def _virtual_path(self, blob_name: str) -> str:
        return from_blob_key(self._config.prefix, blob_name)

    async def _blob_exists(self, container: ContainerClient, blob_key: str) -> bool:
        blob = container.get_blob_client(blob_key)
        return await blob.exists()

    async def _read_blob(self, container: ContainerClient, blob_key: str) -> tuple[str, dict[str, str]]:
        """Download blob content and metadata.

        Returns:
            Tuple of (content_string, metadata_dict).

        Raises:
            ResourceNotFoundError: If blob does not exist.
        """
        blob = container.get_blob_client(blob_key)
        stream = await blob.download_blob(encoding=self._config.encoding)
        content = str(await stream.readall())
        props = await blob.get_blob_properties()
        metadata: dict[str, str] = dict(props.metadata) if props.metadata else {}
        return content, metadata

    async def _write_blob(
        self,
        container: ContainerClient,
        blob_key: str,
        content: str,
        *,
        created_at: Optional[str] = None,
    ) -> None:
        """Upload content to a blob with timestamps in metadata."""
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "created_at": created_at or now,
            "modified_at": now,
        }
        blob = container.get_blob_client(blob_key)
        await blob.upload_blob(
            content.encode(self._config.encoding),
            overwrite=True,
            metadata=metadata,
        )

    async def _list_blobs(
        self,
        container: ContainerClient,
        prefix: str,
    ) -> list[Any]:
        """List all blobs under the given prefix."""
        blobs = []
        async for blob in container.list_blobs(
            name_starts_with=prefix or None,
            include=["metadata"],
        ):
            blobs.append(blob)
        return blobs

    # ------------------------------------------------------------------
    # Sync wrappers
    # ------------------------------------------------------------------

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine from sync context."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            # Already inside an event loop — cannot use asyncio.run().
            # Create a new thread with its own loop.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return asyncio.run(coro)

    # ------------------------------------------------------------------
    # ls_info
    # ------------------------------------------------------------------

    def ls_info(self, path: str) -> list[FileInfo]:
        """List files and subdirectories at *path* (sync wrapper for `als_info`)."""
        return self._run_async(self.als_info(path))

    async def als_info(self, path: str) -> list[FileInfo]:
        """List files and subdirectories at *path*.

        Directories are synthesized from blob key prefixes — no marker blobs
        are required.

        Args:
            path: Virtual directory path (e.g., ``"/src"``).

        Returns:
            Sorted list of `FileInfo` dicts for immediate children.
        """
        container = await self._get_container()
        listing_prefix = get_prefix_for_path(self._config.prefix, path)

        blobs = await self._list_blobs(container, listing_prefix)
        if not blobs:
            return []

        infos: list[FileInfo] = []
        subdirs: set[str] = set()

        # Normalize the virtual directory path
        normalized_path = path if path.endswith("/") else path + "/"
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path

        for blob in blobs:
            virtual = self._virtual_path(blob.name)

            # Get relative path from the listing directory
            if not virtual.startswith(normalized_path):
                continue

            relative = virtual[len(normalized_path) :]
            if not relative:
                continue

            if "/" in relative:
                # Subdirectory — extract immediate child dir name
                subdir_name = relative.split("/")[0]
                subdirs.add(normalized_path + subdir_name + "/")
            else:
                # Direct file in this directory
                modified_at = ""
                if blob.metadata:
                    modified_at = blob.metadata.get("modified_at", "")
                infos.append(
                    build_file_info(
                        path=virtual,
                        is_dir=False,
                        size=blob.size or 0,
                        modified_at=modified_at,
                    )
                )

        # Add synthesized directory entries
        for subdir in sorted(subdirs):
            infos.append(build_file_info(path=subdir, is_dir=True, size=0))

        infos.sort(key=lambda x: x.get("path", ""))
        return infos

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        """Read a file and return its content with line numbers (sync wrapper for `aread`)."""
        return self._run_async(self.aread(file_path, offset, limit))

    async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        """Read a file and return its content with line numbers.

        Args:
            file_path: Virtual path to the file.
            offset: Zero-based line offset to start reading from.
            limit: Maximum number of lines to return.

        Returns:
            File content formatted with line numbers, or an error string if
            the file is not found or the offset is out of range.
        """
        container = await self._get_container()
        blob_key = self._blob_key(file_path)

        try:
            content, _metadata = await self._read_blob(container, blob_key)
        except ResourceNotFoundError:
            return f"Error: File '{file_path}' not found"

        if not content or content.strip() == "":
            return "System reminder: File exists but has empty contents"

        lines = content.split("\n")
        # Remove trailing empty line from split (matches upstream behavior)
        if lines and lines[-1] == "":
            lines = lines[:-1]

        if offset >= len(lines):
            return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

        selected = lines[offset : offset + limit]
        return format_content_with_line_numbers(selected, start_line=offset + 1)

    # ------------------------------------------------------------------
    # write
    # ------------------------------------------------------------------

    def write(self, file_path: str, content: str) -> WriteResult:
        """Create a new file (sync wrapper for `awrite`)."""
        return self._run_async(self.awrite(file_path, content))

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        """Create a new file with the given content.

        Fails if the file already exists — use `aedit` to modify existing files.

        Args:
            file_path: Virtual path for the new file.
            content: UTF-8 text content to write.

        Returns:
            `WriteResult` with the path on success, or an error if the file
            already exists.
        """
        container = await self._get_container()
        blob_key = self._blob_key(file_path)

        if await self._blob_exists(container, blob_key):
            return WriteResult(
                error=f"Cannot write to {file_path} because it already exists. "
                f"Read and then make an edit, or write to a new path."
            )

        await self._write_blob(container, blob_key, content)
        return WriteResult(path=file_path, files_update=None)

    # ------------------------------------------------------------------
    # edit
    # ------------------------------------------------------------------

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        """Replace text in an existing file (sync wrapper for `aedit`)."""
        return self._run_async(self.aedit(file_path, old_string, new_string, replace_all))

    async def aedit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        """Replace text in an existing file.

        Args:
            file_path: Virtual path to the file.
            old_string: The exact substring to find.
            new_string: The replacement text.
            replace_all: If ``True``, replace every occurrence; otherwise
                require exactly one match.

        Returns:
            `EditResult` with the path and occurrence count on success, or an
            error string if the file is not found or the match is ambiguous.
        """
        container = await self._get_container()
        blob_key = self._blob_key(file_path)

        try:
            content, metadata = await self._read_blob(container, blob_key)
        except ResourceNotFoundError:
            return EditResult(error=f"Error: File '{file_path}' not found")

        result = perform_string_replacement(content, old_string, new_string, replace_all)
        if isinstance(result, str):
            return EditResult(error=result)

        new_content, occurrences = result
        created_at = metadata.get("created_at")
        await self._write_blob(container, blob_key, new_content, created_at=created_at)
        return EditResult(path=file_path, files_update=None, occurrences=int(occurrences))

    # ------------------------------------------------------------------
    # glob_info
    # ------------------------------------------------------------------

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching a glob pattern (sync wrapper for `aglob_info`)."""
        return self._run_async(self.aglob_info(pattern, path))

    async def aglob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching a glob pattern.

        Supports ``**`` (globstar) and ``{a,b}`` brace expansion via
        *wcmatch*.

        Args:
            pattern: Glob pattern relative to *path* (e.g., ``"**/*.py"``).
            path: Base directory for the search.

        Returns:
            List of `FileInfo` dicts for matching files.
        """
        container = await self._get_container()
        listing_prefix = get_prefix_for_path(self._config.prefix, path)

        blobs = await self._list_blobs(container, listing_prefix)
        if not blobs:
            return []

        # Normalize the base path for relative matching
        normalized_path = path if path.startswith("/") else "/" + path
        normalized_path = normalized_path.rstrip("/") if normalized_path != "/" else "/"

        infos: list[FileInfo] = []
        for blob in blobs:
            virtual = self._virtual_path(blob.name)

            # Compute relative path for glob matching
            if normalized_path == "/":
                relative = virtual[1:]  # Remove leading /
            else:
                prefix_with_slash = normalized_path + "/"
                if virtual.startswith(prefix_with_slash):
                    relative = virtual[len(prefix_with_slash) :]
                elif virtual == normalized_path:
                    relative = virtual.split("/")[-1]
                else:
                    continue

            if wcglob.globmatch(relative, pattern, flags=wcglob.BRACE | wcglob.GLOBSTAR):
                modified_at = ""
                if blob.metadata:
                    modified_at = blob.metadata.get("modified_at", "")
                infos.append(
                    build_file_info(
                        path=virtual,
                        is_dir=False,
                        size=blob.size or 0,
                        modified_at=modified_at,
                    )
                )

        return infos

    # ------------------------------------------------------------------
    # grep_raw
    # ------------------------------------------------------------------

    def grep_raw(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> list[GrepMatch] | str:
        """Search file contents for a literal substring (sync wrapper for `agrep_raw`)."""
        return self._run_async(self.agrep_raw(pattern, path, glob))

    async def agrep_raw(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> list[GrepMatch] | str:
        """Search file contents for a literal substring.

        Blobs are downloaded and scanned concurrently (bounded by
        ``AzureBlobConfig.max_concurrency``).

        Args:
            pattern: Literal substring to search for.
            path: Directory scope for the search (default: ``"/"``).
            glob: Optional filename glob to pre-filter blobs (e.g.,
                ``"*.py"``).

        Returns:
            List of `GrepMatch` dicts with ``path``, ``line``, and ``text``
            keys, or an empty list if nothing matches.
        """
        container = await self._get_container()
        search_path = path if path is not None else "/"
        listing_prefix = get_prefix_for_path(self._config.prefix, search_path)

        blobs = await self._list_blobs(container, listing_prefix)
        if not blobs:
            return []

        # Filter by glob pattern on filename if provided
        if glob:
            from pathlib import PurePosixPath

            blobs = [
                b
                for b in blobs
                if wcglob.globmatch(
                    PurePosixPath(b.name).name,
                    glob,
                    flags=wcglob.BRACE,
                )
            ]

        matches: list[GrepMatch] = []

        # Process blobs concurrently with bounded concurrency
        semaphore = asyncio.Semaphore(self._config.max_concurrency)

        async def search_blob(blob: Any) -> list[GrepMatch]:
            async with semaphore:
                try:
                    blob_client = container.get_blob_client(blob.name)
                    stream = await blob_client.download_blob(
                        encoding=self._config.encoding,
                    )
                    content = str(await stream.readall())
                except Exception:
                    logger.debug("Failed to read blob %s for grep", blob.name)
                    return []

                virtual = self._virtual_path(blob.name)
                blob_matches: list[GrepMatch] = []
                for line_num, line in enumerate(content.split("\n"), 1):
                    if pattern in line:  # Literal substring match
                        blob_matches.append({"path": virtual, "line": line_num, "text": line})
                return blob_matches

        results = await asyncio.gather(*(search_blob(b) for b in blobs))
        for blob_matches in results:
            matches.extend(blob_matches)

        return matches

    # ------------------------------------------------------------------
    # upload_files / download_files
    # ------------------------------------------------------------------

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload binary files (sync wrapper for `aupload_files`)."""
        return self._run_async(self.aupload_files(files))

    async def aupload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload one or more binary files, overwriting if they exist.

        Args:
            files: List of ``(path, content_bytes)`` tuples.

        Returns:
            List of `FileUploadResponse` dicts, one per input file.
        """
        container = await self._get_container()
        responses: list[FileUploadResponse] = []

        for file_path, content in files:
            blob_key = self._blob_key(file_path)
            now = datetime.now(timezone.utc).isoformat()
            metadata = {"created_at": now, "modified_at": now}

            try:
                blob = container.get_blob_client(blob_key)
                await blob.upload_blob(content, overwrite=True, metadata=metadata)
                responses.append(FileUploadResponse(path=file_path, error=None))
            except Exception as exc:
                logger.error("Failed to upload %s: %s", file_path, exc)
                responses.append(FileUploadResponse(path=file_path, error="permission_denied"))

        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files as raw bytes (sync wrapper for `adownload_files`)."""
        return self._run_async(self.adownload_files(paths))

    async def adownload_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download one or more files as raw bytes.

        Args:
            paths: Virtual paths to download.

        Returns:
            List of `FileDownloadResponse` dicts. Each contains ``content``
            (bytes) on success, or ``error`` set to ``"file_not_found"``.
        """
        container = await self._get_container()
        responses: list[FileDownloadResponse] = []

        for file_path in paths:
            blob_key = self._blob_key(file_path)
            try:
                blob = container.get_blob_client(blob_key)
                stream = await blob.download_blob()
                raw = await stream.readall()
                content_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
                responses.append(FileDownloadResponse(path=file_path, content=content_bytes, error=None))
            except ResourceNotFoundError:
                responses.append(FileDownloadResponse(path=file_path, content=None, error="file_not_found"))

        return responses

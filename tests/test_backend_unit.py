"""Unit tests for AzureBlobBackend (mocked, no I/O)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig
from deepagents_azure_blob_backend._path import (
    from_blob_key,
    get_prefix_for_path,
    normalize_path,
    to_blob_key,
)
from deepagents_azure_blob_backend._utils import build_file_info

# ------------------------------------------------------------------
# Path utility tests
# ------------------------------------------------------------------


class TestNormalizePath:
    def test_strips_leading_slash(self):
        assert normalize_path("/src/main.py") == "src/main.py"

    def test_no_leading_slash(self):
        assert normalize_path("src/main.py") == "src/main.py"

    def test_root(self):
        assert normalize_path("/") == ""

    def test_double_slashes(self):
        assert normalize_path("//src//main.py") == "src/main.py"

    def test_trailing_slash(self):
        assert normalize_path("/src/") == "src"

    def test_empty_string(self):
        assert normalize_path("") == ""

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="Path traversal"):
            normalize_path("/src/../secrets.txt")

    def test_rejects_windows_absolute_path(self):
        with pytest.raises(ValueError, match="Windows absolute paths"):
            normalize_path("C:/temp/file.txt")


class TestToBlobKey:
    def test_with_prefix(self):
        assert to_blob_key("workspace/", "/src/main.py") == "workspace/src/main.py"

    def test_without_prefix(self):
        assert to_blob_key("", "/src/main.py") == "src/main.py"

    def test_prefix_no_trailing_slash(self):
        assert to_blob_key("workspace", "/src/main.py") == "workspace/src/main.py"


class TestFromBlobKey:
    def test_with_prefix(self):
        assert from_blob_key("workspace/", "workspace/src/main.py") == "/src/main.py"

    def test_without_prefix(self):
        assert from_blob_key("", "src/main.py") == "/src/main.py"

    def test_prefix_no_trailing_slash(self):
        assert from_blob_key("workspace", "workspace/src/main.py") == "/src/main.py"


class TestGetPrefixForPath:
    def test_root_with_prefix(self):
        assert get_prefix_for_path("workspace/", "/") == "workspace/"

    def test_subdir_with_prefix(self):
        assert get_prefix_for_path("workspace/", "/src") == "workspace/src/"

    def test_root_no_prefix(self):
        assert get_prefix_for_path("", "/") == ""

    def test_subdir_no_prefix(self):
        assert get_prefix_for_path("", "/src") == "src/"


# ------------------------------------------------------------------
# Config tests
# ------------------------------------------------------------------


class TestAzureBlobConfig:
    def test_defaults(self):
        from deepagents_azure_blob_backend import AzureBlobConfig

        config = AzureBlobConfig()
        assert config.account_url == ""
        assert config.container_name == ""
        assert config.prefix == ""
        assert config.credential is None
        assert config.max_concurrency == 8
        assert config.encoding == "utf-8"
        assert config.connection_string is None

    def test_custom_values(self):
        from deepagents_azure_blob_backend import AzureBlobConfig

        config = AzureBlobConfig(
            account_url="https://myaccount.blob.core.windows.net",
            container_name="mycontainer",
            prefix="agent-1/",
            max_concurrency=4,
        )
        assert config.account_url == "https://myaccount.blob.core.windows.net"
        assert config.container_name == "mycontainer"
        assert config.prefix == "agent-1/"
        assert config.max_concurrency == 4


# ------------------------------------------------------------------
# Backend class tests (no I/O)
# ------------------------------------------------------------------


class TestAzureBlobBackendInit:
    def test_is_backend_protocol(self):
        from deepagents.backends.protocol import BackendProtocol

        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
        )
        backend = AzureBlobBackend(config)
        assert isinstance(backend, BackendProtocol)

    def test_credential_is_none_on_init(self):
        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
        )
        backend = AzureBlobBackend(config)
        assert backend._credential is None


class TestAzureBlobBackendClose:
    """Tests for the close() lifecycle of AzureBlobBackend."""

    async def test_close_calls_credential_close(self):
        """close() must await the stored credential's close() coroutine."""
        from unittest.mock import AsyncMock

        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
        )
        backend = AzureBlobBackend(config)

        mock_credential = AsyncMock()
        mock_credential.close = AsyncMock()
        backend._credential = mock_credential

        await backend.close()

        mock_credential.close.assert_awaited_once()
        assert backend._credential is None

    async def test_close_is_safe_without_credential(self):
        """close() must not raise when _credential is None."""
        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
        )
        backend = AzureBlobBackend(config)
        # Should not raise even with no client or credential initialised.
        await backend.close()

    async def test_get_container_stores_default_credential(self):
        """When no credential is configured, _get_container() stores the
        auto-created DefaultAzureCredential on self._credential."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
        )
        backend = AzureBlobBackend(config)

        mock_credential = AsyncMock()
        mock_container = MagicMock()
        mock_client = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        with (
            patch(
                "deepagents_azure_blob_backend.backend.BlobServiceClient",
                return_value=mock_client,
            ),
            patch(
                "azure.identity.aio.DefaultAzureCredential",
                return_value=mock_credential,
            ),
        ):
            await backend._get_container()

        assert backend._credential is mock_credential

    async def test_get_container_stores_async_user_credential(self):
        """When the user supplies an async credential, _get_container() stores
        it on self._credential so that close() can release its resources."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        mock_credential = AsyncMock()

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
            credential=mock_credential,
        )
        backend = AzureBlobBackend(config)

        mock_container = MagicMock()
        mock_client = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        with patch(
            "deepagents_azure_blob_backend.backend.BlobServiceClient",
            return_value=mock_client,
        ):
            await backend._get_container()

        assert backend._credential is mock_credential

    async def test_get_container_does_not_store_sync_credential(self):
        """Sync (non-async) credentials are not stored on self._credential,
        since they do not own an async HTTP session."""
        from unittest.mock import MagicMock, patch

        from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

        sync_credential = MagicMock()
        # Ensure close is a plain (non-coroutine) callable
        sync_credential.close = MagicMock()

        config = AzureBlobConfig(
            account_url="https://test.blob.core.windows.net",
            container_name="test",
            credential=sync_credential,
        )
        backend = AzureBlobBackend(config)

        mock_container = MagicMock()
        mock_client = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        with patch(
            "deepagents_azure_blob_backend.backend.BlobServiceClient",
            return_value=mock_client,
        ):
            await backend._get_container()

        assert backend._credential is None


# ------------------------------------------------------------------
# build_file_info tests
# ------------------------------------------------------------------


class TestBuildFileInfo:
    def test_defaults(self):
        info = build_file_info("/src/main.py")
        assert info == {"path": "/src/main.py", "is_dir": False, "size": 0, "modified_at": ""}

    def test_directory(self):
        info = build_file_info("/src/", is_dir=True, size=0)
        assert info["is_dir"] is True

    def test_custom_values(self):
        info = build_file_info("/f.txt", size=100, modified_at="2026-01-01T00:00:00Z")
        assert info["size"] == 100
        assert info["modified_at"] == "2026-01-01T00:00:00Z"


# ------------------------------------------------------------------
# Helpers for mocked backend tests
# ------------------------------------------------------------------


def _make_backend(prefix: str = "pfx/") -> AzureBlobBackend:
    config = AzureBlobConfig(
        account_url="https://test.blob.core.windows.net",
        container_name="test",
        prefix=prefix,
        connection_string="DefaultEndpointsProtocol=https;AccountName=fake;AccountKey=ZmFrZQ==;",
    )
    return AzureBlobBackend(config)


def _make_blob(name: str, content: str = "", size: int = 0, metadata: dict | None = None):
    """Create a mock blob object."""
    blob = MagicMock()
    blob.name = name
    blob.size = size
    blob.metadata = metadata
    blob._content = content
    return blob


async def _setup_backend_with_container(prefix: str = "pfx/"):
    """Create a backend with a pre-injected mock container.

    Uses MagicMock for the container because get_blob_client() is synchronous
    in the real Azure SDK. Async methods (exists, download_blob, etc.) are
    configured on individual blob client mocks in each test.
    """
    backend = _make_backend(prefix)
    container = MagicMock()
    backend._container = container
    backend._client = AsyncMock()
    return backend, container


# ------------------------------------------------------------------
# _get_container tests
# ------------------------------------------------------------------


class TestGetContainer:
    async def test_returns_cached_container(self):
        backend, container = await _setup_backend_with_container()
        result = await backend._get_container()
        assert result is container

    async def test_connection_string_path(self):
        backend = _make_backend()
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        with patch("deepagents_azure_blob_backend.backend.BlobServiceClient") as MockBSC:
            MockBSC.from_connection_string.return_value = mock_client
            result = await backend._get_container()

        assert result is mock_container
        MockBSC.from_connection_string.assert_called_once()

    async def test_double_checked_locking(self):
        """Second call inside the lock returns cached container."""
        backend = _make_backend()
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.get_container_client.return_value = mock_container

        with patch("deepagents_azure_blob_backend.backend.BlobServiceClient") as MockBSC:
            MockBSC.from_connection_string.return_value = mock_client
            c1 = await backend._get_container()
            c2 = await backend._get_container()

        assert c1 is c2
        MockBSC.from_connection_string.assert_called_once()

    async def test_concurrent_init_double_check(self):
        """Cover line 73: second task finds container set inside the lock."""
        import asyncio

        backend = _make_backend()
        mock_container = MagicMock()

        # Hold the lock, let a task queue behind us, then set container
        async with backend._init_lock:
            # Task starts: passes outer check (container is None), blocks on lock
            task = asyncio.create_task(backend._get_container())
            await asyncio.sleep(0)  # Let task run until it blocks on the lock
            # Set container while we hold the lock
            backend._container = mock_container
        # Lock released: task acquires it, inner check finds container set → line 73
        result = await task
        assert result is mock_container


# ------------------------------------------------------------------
# close tests (with client)
# ------------------------------------------------------------------


class TestCloseWithClient:
    async def test_close_clears_client_and_container(self):
        backend, _ = await _setup_backend_with_container()
        await backend.close()
        assert backend._client is None
        assert backend._container is None


# ------------------------------------------------------------------
# Helper method tests
# ------------------------------------------------------------------


class TestHelperMethods:
    def test_blob_key(self):
        backend = _make_backend("pfx/")
        assert backend._blob_key("/src/main.py") == "pfx/src/main.py"

    def test_virtual_path(self):
        backend = _make_backend("pfx/")
        assert backend._virtual_path("pfx/src/main.py") == "/src/main.py"

    async def test_blob_exists_true(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.exists.return_value = True
        container.get_blob_client.return_value = mock_blob
        assert await backend._blob_exists(container, "pfx/file.txt") is True

    async def test_blob_exists_false(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.exists.return_value = False
        container.get_blob_client.return_value = mock_blob
        assert await backend._blob_exists(container, "pfx/file.txt") is False

    async def test_read_blob(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "hello world"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {"created_at": "t1", "modified_at": "t2"}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        content, metadata = await backend._read_blob(container, "pfx/file.txt")
        assert content == "hello world"
        assert metadata == {"created_at": "t1", "modified_at": "t2"}

    async def test_read_blob_no_metadata(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "data"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = None
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        content, metadata = await backend._read_blob(container, "pfx/file.txt")
        assert content == "data"
        assert metadata == {}

    async def test_write_blob(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        await backend._write_blob(container, "pfx/file.txt", "content")
        mock_blob.upload_blob.assert_awaited_once()
        call_kwargs = mock_blob.upload_blob.call_args
        assert call_kwargs.kwargs["overwrite"] is True
        assert "created_at" in call_kwargs.kwargs["metadata"]

    async def test_write_blob_preserves_created_at(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        await backend._write_blob(container, "pfx/file.txt", "content", created_at="original")
        call_kwargs = mock_blob.upload_blob.call_args
        assert call_kwargs.kwargs["metadata"]["created_at"] == "original"

    async def test_list_blobs(self):
        backend, container = await _setup_backend_with_container()
        blob1 = _make_blob("pfx/a.txt")
        blob2 = _make_blob("pfx/b.txt")

        async def fake_list_blobs(**kwargs):
            for b in [blob1, blob2]:
                yield b

        container.list_blobs = fake_list_blobs
        result = await backend._list_blobs(container, "pfx/")
        assert len(result) == 2

    async def test_list_blobs_empty_prefix(self):
        backend, container = await _setup_backend_with_container()

        async def fake_list_blobs(**kwargs):
            assert kwargs.get("name_starts_with") is None
            return
            yield  # make it an async generator

        container.list_blobs = fake_list_blobs
        result = await backend._list_blobs(container, "")
        assert result == []


# ------------------------------------------------------------------
# _run_async tests
# ------------------------------------------------------------------


class TestRunAsync:
    def test_run_async_no_loop(self):
        backend = _make_backend()

        async def coro():
            return 42

        assert backend._run_async(coro()) == 42

    def test_run_async_nested_loop(self):
        """_run_async uses a thread when already inside an event loop."""
        import asyncio

        backend = _make_backend()

        async def inner():
            return 99

        async def outer():
            return backend._run_async(inner())

        result = asyncio.run(outer())
        assert result == 99


# ------------------------------------------------------------------
# aread tests
# ------------------------------------------------------------------


class TestARead:
    async def test_read_success(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "line1\nline2\nline3\n"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        result = await backend.aread("/file.txt")
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    async def test_read_not_found(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.download_blob.side_effect = ResourceNotFoundError("not found")
        container.get_blob_client.return_value = mock_blob

        result = await backend.aread("/missing.txt")
        assert "Error" in result
        assert "not found" in result.lower()

    async def test_read_empty_file(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = ""
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        result = await backend.aread("/empty.txt")
        assert "empty" in result.lower()

    async def test_read_with_offset_and_limit(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "line1\nline2\nline3\nline4\nline5\n"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        result = await backend.aread("/file.txt", offset=1, limit=2)
        assert "line2" in result
        assert "line3" in result
        assert "line1" not in result

    async def test_read_offset_out_of_range(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "line1\n"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        result = await backend.aread("/file.txt", offset=100)
        assert "Error" in result
        assert "offset" in result.lower()

    async def test_read_invalid_path(self):
        backend, _ = await _setup_backend_with_container()

        result = await backend.aread("/src/../bad.txt")
        assert "invalid path" in result.lower()


# ------------------------------------------------------------------
# awrite tests
# ------------------------------------------------------------------


class TestAWrite:
    async def test_write_new_file(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.upload_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        result = await backend.awrite("/new.txt", "hello")
        assert result.path == "/new.txt"
        assert result.error is None

    async def test_write_existing_file_fails(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.upload_blob.side_effect = ResourceExistsError("exists")
        container.get_blob_client.return_value = mock_blob

        result = await backend.awrite("/existing.txt", "hello")
        assert result.error is not None
        assert "already exists" in result.error

    async def test_write_invalid_path_fails(self):
        backend, _ = await _setup_backend_with_container()

        result = await backend.awrite("/src/../bad.txt", "hello")
        assert result.error is not None
        assert "invalid path" in result.error.lower()


# ------------------------------------------------------------------
# aedit tests
# ------------------------------------------------------------------


class TestAEdit:
    async def test_edit_success(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "hello world"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {"created_at": "t1", "modified_at": "t2"}
        mock_blob.get_blob_properties.return_value = mock_props
        mock_blob.upload_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        result = await backend.aedit("/file.txt", "hello", "goodbye")
        assert result.path == "/file.txt"
        assert result.error is None

    async def test_edit_not_found(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.download_blob.side_effect = ResourceNotFoundError("not found")
        container.get_blob_client.return_value = mock_blob

        result = await backend.aedit("/missing.txt", "a", "b")
        assert result.error is not None
        assert "not found" in result.error.lower()

    async def test_edit_string_not_found(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "hello world"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        result = await backend.aedit("/file.txt", "nonexistent", "replacement")
        assert result.error is not None

    async def test_edit_multiple_occurrences_fails(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "aaa"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {}
        mock_blob.get_blob_properties.return_value = mock_props
        container.get_blob_client.return_value = mock_blob

        result = await backend.aedit("/file.txt", "a", "b", replace_all=False)
        assert result.error is not None

    async def test_edit_replace_all(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "aaa"
        mock_blob.download_blob.return_value = mock_stream
        mock_props = MagicMock()
        mock_props.metadata = {"created_at": "t1"}
        mock_blob.get_blob_properties.return_value = mock_props
        mock_blob.upload_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        result = await backend.aedit("/file.txt", "a", "b", replace_all=True)
        assert result.path == "/file.txt"
        assert result.occurrences == 3

    async def test_edit_invalid_path(self):
        backend, _ = await _setup_backend_with_container()

        result = await backend.aedit("/src/../bad.txt", "a", "b")
        assert result.error is not None
        assert "invalid path" in result.error.lower()


# ------------------------------------------------------------------
# als_info tests
# ------------------------------------------------------------------


class TestALsInfo:
    async def test_ls_files(self):
        backend, container = await _setup_backend_with_container()
        blob1 = _make_blob("pfx/src/a.py", size=100, metadata={"modified_at": "t1"})
        blob2 = _make_blob("pfx/src/b.py", size=200, metadata={"modified_at": "t2"})

        async def fake_list(**kwargs):
            for b in [blob1, blob2]:
                yield b

        container.list_blobs = fake_list
        result = await backend.als_info("/src")
        assert len(result) == 2
        paths = [r["path"] for r in result]
        assert "/src/a.py" in paths
        assert "/src/b.py" in paths

    async def test_ls_synthesizes_directories(self):
        backend, container = await _setup_backend_with_container()
        blob1 = _make_blob("pfx/src/sub/a.py", size=50)
        blob2 = _make_blob("pfx/src/b.py", size=100, metadata={"modified_at": "t1"})

        async def fake_list(**kwargs):
            for b in [blob1, blob2]:
                yield b

        container.list_blobs = fake_list
        result = await backend.als_info("/src")
        dirs = [r for r in result if r["is_dir"]]
        files = [r for r in result if not r["is_dir"]]
        assert len(dirs) == 1
        assert dirs[0]["path"] == "/src/sub/"
        assert len(files) == 1

    async def test_ls_empty(self):
        backend, container = await _setup_backend_with_container()

        async def fake_list(**kwargs):
            return
            yield

        container.list_blobs = fake_list
        result = await backend.als_info("/empty")
        assert result == []

    async def test_ls_path_without_leading_slash(self):
        """Cover line 236: path without leading /."""
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/src/a.py", size=100, metadata={"modified_at": "t1"})

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.als_info("src")
        assert len(result) == 1
        assert result[0]["path"] == "/src/a.py"

    async def test_ls_skips_non_matching_blobs(self):
        """Cover line 243: blobs that don't start with normalized_path."""
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/other/a.py", size=100)

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.als_info("/src")
        assert result == []

    async def test_ls_skips_empty_relative(self):
        """Cover line 247: blob whose virtual path equals the normalized directory path."""
        backend, container = await _setup_backend_with_container()
        # Blob key "pfx/src/" → virtual "/src/" which equals normalized_path "/src/"
        # so relative becomes "" and is skipped at line 246-247
        blob = _make_blob("pfx/src/", size=0)

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.als_info("/src")
        assert result == []

    async def test_ls_no_metadata(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/src/a.py", size=50, metadata=None)

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.als_info("/src")
        assert len(result) == 1
        assert result[0]["modified_at"] == ""


# ------------------------------------------------------------------
# aglob_info tests
# ------------------------------------------------------------------


class TestAGlobInfo:
    async def test_glob_pattern(self):
        backend, container = await _setup_backend_with_container()
        blob1 = _make_blob("pfx/src/a.py", size=100, metadata={"modified_at": "t1"})
        blob2 = _make_blob("pfx/src/b.txt", size=50)

        async def fake_list(**kwargs):
            for b in [blob1, blob2]:
                yield b

        container.list_blobs = fake_list
        result = await backend.aglob_info("*.py", path="/src")
        assert len(result) == 1
        assert result[0]["path"] == "/src/a.py"

    async def test_glob_recursive(self):
        backend, container = await _setup_backend_with_container()
        blob1 = _make_blob("pfx/a.py", size=100, metadata={"modified_at": "t1"})
        blob2 = _make_blob("pfx/sub/b.py", size=50, metadata={"modified_at": "t2"})
        blob3 = _make_blob("pfx/sub/c.txt", size=25)

        async def fake_list(**kwargs):
            for b in [blob1, blob2, blob3]:
                yield b

        container.list_blobs = fake_list
        result = await backend.aglob_info("**/*.py", path="/")
        paths = [r["path"] for r in result]
        assert "/a.py" in paths
        assert "/sub/b.py" in paths
        assert len(result) == 2

    async def test_glob_empty(self):
        backend, container = await _setup_backend_with_container()

        async def fake_list(**kwargs):
            return
            yield

        container.list_blobs = fake_list
        result = await backend.aglob_info("*.py")
        assert result == []

    async def test_glob_no_metadata(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/a.py", size=100, metadata=None)

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.aglob_info("*.py", path="/")
        assert len(result) == 1
        assert result[0]["modified_at"] == ""

    async def test_glob_exact_path_match(self):
        """Cover line 443-444: virtual == normalized_path."""
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/src/main.py", size=100, metadata={"modified_at": "t1"})

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.aglob_info("main.py", path="/src/main.py")
        assert len(result) == 1

    async def test_glob_skips_non_matching_prefix(self):
        """Cover lines 445-446: blob outside the search path."""
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/other/a.py", size=100)

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.aglob_info("*.py", path="/src")
        assert result == []

    async def test_glob_no_match(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/a.txt", size=100)

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        result = await backend.aglob_info("*.py", path="/")
        assert result == []


# ------------------------------------------------------------------
# agrep_raw tests
# ------------------------------------------------------------------


class TestAGrepRaw:
    async def test_grep_finds_matches(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/file.py", size=50)
        mock_blob_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "hello world\ngoodbye world\nhello again\n"
        mock_blob_client.download_blob.return_value = mock_stream

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        container.get_blob_client.return_value = mock_blob_client

        result = await backend.agrep_raw("hello")
        assert len(result) == 2
        assert result[0]["line"] == 1
        assert result[1]["line"] == 3

    async def test_grep_with_glob_filter(self):
        backend, container = await _setup_backend_with_container()
        blob_py = _make_blob("pfx/file.py", size=50)
        blob_txt = _make_blob("pfx/file.txt", size=50)
        mock_blob_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "match here\n"
        mock_blob_client.download_blob.return_value = mock_stream

        async def fake_list(**kwargs):
            for b in [blob_py, blob_txt]:
                yield b

        container.list_blobs = fake_list
        container.get_blob_client.return_value = mock_blob_client

        result = await backend.agrep_raw("match", glob="*.py")
        assert len(result) == 1
        assert result[0]["path"] == "/file.py"

    async def test_grep_with_path_aware_glob_filter(self):
        backend, container = await _setup_backend_with_container()
        blob_nested = _make_blob("pfx/src/lib/file.py", size=50)
        blob_top = _make_blob("pfx/src/file.py", size=50)
        mock_blob_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "match here\n"
        mock_blob_client.download_blob.return_value = mock_stream

        async def fake_list(**kwargs):
            for blob in [blob_nested, blob_top]:
                yield blob

        container.list_blobs = fake_list
        container.get_blob_client.return_value = mock_blob_client

        result = await backend.agrep_raw("match", path="/", glob="src/*/*.py")
        assert isinstance(result, list)
        assert [match["path"] for match in result] == ["/src/lib/file.py"]

    async def test_grep_no_matches(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/file.py", size=50)
        mock_blob_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "nothing here\n"
        mock_blob_client.download_blob.return_value = mock_stream

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        container.get_blob_client.return_value = mock_blob_client

        result = await backend.agrep_raw("missing")
        assert result == []

    async def test_grep_empty_listing(self):
        backend, container = await _setup_backend_with_container()

        async def fake_list(**kwargs):
            return
            yield

        container.list_blobs = fake_list
        result = await backend.agrep_raw("pattern")
        assert result == []

    async def test_grep_blob_read_failure(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/file.py", size=50)
        mock_blob_client = AsyncMock()
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("read error")

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        container.get_blob_client.return_value = mock_blob_client

        result = await backend.agrep_raw("pattern")
        assert isinstance(result, str)
        assert "could not read 1 file" in result.lower()
        assert "/file.py" in result

    async def test_grep_with_path(self):
        backend, container = await _setup_backend_with_container()
        blob = _make_blob("pfx/src/file.py", size=50)
        mock_blob_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "match\n"
        mock_blob_client.download_blob.return_value = mock_stream

        async def fake_list(**kwargs):
            yield blob

        container.list_blobs = fake_list
        container.get_blob_client.return_value = mock_blob_client

        result = await backend.agrep_raw("match", path="/src")
        assert len(result) == 1

    async def test_grep_invalid_path(self):
        backend, _ = await _setup_backend_with_container()

        result = await backend.agrep_raw("match", path="/src/../bad")
        assert isinstance(result, str)
        assert "invalid path" in result.lower()


# ------------------------------------------------------------------
# aupload_files tests
# ------------------------------------------------------------------


class TestAUploadFiles:
    async def test_upload_success(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        result = await backend.aupload_files([("/file.bin", b"binary data")])
        assert len(result) == 1
        assert result[0].path == "/file.bin"
        assert result[0].error is None

    async def test_upload_failure(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.upload_blob.side_effect = Exception("upload failed")
        container.get_blob_client.return_value = mock_blob

        result = await backend.aupload_files([("/file.bin", b"data")])
        assert len(result) == 1
        assert result[0].error == "permission_denied"

    async def test_upload_multiple_files(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        container.get_blob_client.return_value = mock_blob

        files = [("/a.bin", b"aaa"), ("/b.bin", b"bbb")]
        result = await backend.aupload_files(files)
        assert len(result) == 2
        assert all(r.error is None for r in result)

    async def test_upload_invalid_path(self):
        backend, _ = await _setup_backend_with_container()

        result = await backend.aupload_files([("/src/../bad.bin", b"data")])
        assert result[0].error == "invalid_path"


# ------------------------------------------------------------------
# adownload_files tests
# ------------------------------------------------------------------


class TestADownloadFiles:
    async def test_download_success(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = b"file content"
        mock_blob.download_blob.return_value = mock_stream
        container.get_blob_client.return_value = mock_blob

        result = await backend.adownload_files(["/file.txt"])
        assert len(result) == 1
        assert result[0].content == b"file content"
        assert result[0].error is None

    async def test_download_not_found(self):
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_blob.download_blob.side_effect = ResourceNotFoundError("not found")
        container.get_blob_client.return_value = mock_blob

        result = await backend.adownload_files(["/missing.txt"])
        assert len(result) == 1
        assert result[0].error == "file_not_found"
        assert result[0].content is None

    async def test_download_string_content_encoded(self):
        """When readall returns a string, it should be encoded to bytes."""
        backend, container = await _setup_backend_with_container()
        mock_blob = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.readall.return_value = "string content"
        mock_blob.download_blob.return_value = mock_stream
        container.get_blob_client.return_value = mock_blob

        result = await backend.adownload_files(["/file.txt"])
        assert result[0].content == b"string content"

    async def test_download_invalid_path(self):
        backend, _ = await _setup_backend_with_container()

        result = await backend.adownload_files(["/src/../bad.txt"])
        assert result[0].error == "invalid_path"


# ------------------------------------------------------------------
# Sync wrapper tests
# ------------------------------------------------------------------


class TestSyncWrappers:
    def test_read_sync(self):
        backend = _make_backend()
        backend.aread = AsyncMock(return_value="line content")
        result = backend.read("/file.txt")
        assert result == "line content"

    def test_write_sync(self):
        backend = _make_backend()
        backend.awrite = AsyncMock(return_value={"path": "/f.txt", "error": None, "files_update": None})
        result = backend.write("/f.txt", "content")
        assert result["path"] == "/f.txt"

    def test_edit_sync(self):
        backend = _make_backend()
        backend.aedit = AsyncMock(
            return_value={"path": "/f.txt", "error": None, "files_update": None, "occurrences": 1}
        )
        result = backend.edit("/f.txt", "a", "b")
        assert result["path"] == "/f.txt"

    def test_ls_info_sync(self):
        backend = _make_backend()
        backend.als_info = AsyncMock(return_value=[])
        result = backend.ls_info("/")
        assert result == []

    def test_glob_info_sync(self):
        backend = _make_backend()
        backend.aglob_info = AsyncMock(return_value=[])
        result = backend.glob_info("*.py")
        assert result == []

    def test_grep_raw_sync(self):
        backend = _make_backend()
        backend.agrep_raw = AsyncMock(return_value=[])
        result = backend.grep_raw("pattern")
        assert result == []

    def test_upload_files_sync(self):
        backend = _make_backend()
        backend.aupload_files = AsyncMock(return_value=[])
        result = backend.upload_files([])
        assert result == []

    def test_download_files_sync(self):
        backend = _make_backend()
        backend.adownload_files = AsyncMock(return_value=[])
        result = backend.download_files([])
        assert result == []

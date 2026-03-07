"""Unit tests for AzureBlobBackend (mocked, no I/O)."""

from __future__ import annotations

from deepagents_azure_blob_backend._path import (
    from_blob_key,
    get_prefix_for_path,
    normalize_path,
    to_blob_key,
)

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

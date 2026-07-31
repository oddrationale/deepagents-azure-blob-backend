"""Unit tests for the package-level deprecation notice."""

from __future__ import annotations

import importlib

import pytest

import deepagents_azure_blob_backend


class TestDeprecationWarning:
    def test_import_warns(self):
        # The warning fires at module exec time, so a plain import is a no-op once
        # another test has already imported the package.
        with pytest.warns(DeprecationWarning, match="langchain-azure-storage"):
            importlib.reload(deepagents_azure_blob_backend)

    def test_reload_still_exports_public_api(self):
        module = importlib.reload(deepagents_azure_blob_backend)
        assert module.__all__ == ["AzureBlobBackend", "AzureBlobConfig"]

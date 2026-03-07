"""Configuration for the Azure Blob Storage backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AzureBlobConfig:
    """Configuration for AzureBlobBackend."""

    account_url: str = ""
    """Azure Blob Storage account URL (e.g., `https://<account>.blob.core.windows.net`)."""

    container_name: str = ""
    """Target blob container name."""

    prefix: str = ""
    """Key namespace prefix within the container.
    Supports multi-agent isolation by scoping each agent to a prefix."""

    credential: Any = None
    """Azure credential object. If `None`, `DefaultAzureCredential` is used automatically."""

    max_concurrency: int = 8
    """Maximum parallel blob operations for grep/glob."""

    encoding: str = "utf-8"
    """Text encoding for blob content."""

    connection_string: Optional[str] = None
    """Optional connection string override. When set, `account_url` and `credential`
    are ignored. Useful for Azurite testing."""

    api_version: str = "2025-11-05"
    """Azure Storage API version string."""

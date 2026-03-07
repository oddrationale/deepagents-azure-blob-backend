"""Configuration for the Azure Blob Storage backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AzureBlobConfig:
    """Configuration for AzureBlobBackend.

    Attributes:
        account_url: Azure Blob Storage account URL
            (e.g., https://<account>.blob.core.windows.net).
        container_name: Target blob container name.
        prefix: Key namespace prefix within the container. Supports
            multi-agent isolation by scoping each agent to a prefix.
        credential: Azure credential object. If None, DefaultAzureCredential
            is used automatically.
        max_concurrency: Maximum parallel blob operations for grep/glob.
        encoding: Text encoding for blob content.
        connection_string: Optional connection string override. When set,
            account_url and credential are ignored. Useful for Azurite testing.
    """

    account_url: str = ""
    container_name: str = ""
    prefix: str = ""
    credential: Any = None
    max_concurrency: int = 8
    encoding: str = "utf-8"
    connection_string: Optional[str] = None
    api_version: str = "2025-11-05"

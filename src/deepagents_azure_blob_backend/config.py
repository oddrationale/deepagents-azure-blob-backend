"""Configuration for the Azure Blob Storage backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AzureBlobConfig:
    """Configuration for AzureBlobBackend.

    Five authentication methods are supported (mutually exclusive):

    1. **Connection string** — set ``connection_string``. Everything else
       (``account_url``, credentials) is derived from the string.
    2. **Account key** — set ``account_url`` + ``account_key``.
    3. **SAS token** — set ``account_url`` + ``sas_token``.
    4. **Credential object** — set ``account_url`` + ``credential`` (any
       Azure credential instance, e.g. ``ClientSecretCredential``).
    5. **Default (AAD)** — set ``account_url`` only. Uses
       ``DefaultAzureCredential`` automatically.

    Raises:
        ValueError: If more than one credential source is provided, or if
            ``account_url`` is missing when required.
    """

    account_url: str = ""
    """Azure Blob Storage account URL (e.g., `https://<account>.blob.core.windows.net`)."""

    container_name: str = ""
    """Target blob container name."""

    prefix: str = ""
    """Key namespace prefix within the container.
    Supports multi-agent isolation by scoping each agent to a prefix."""

    credential: Any = None
    """Azure credential object (e.g., ``ClientSecretCredential``).
    Mutually exclusive with ``connection_string``, ``account_key``, and ``sas_token``."""

    account_key: Optional[str] = None
    """Azure Storage account key for shared-key authentication.
    Mutually exclusive with ``connection_string``, ``sas_token``, and ``credential``."""

    sas_token: Optional[str] = None
    """Shared Access Signature token string (**without** leading ``?``).
    Mutually exclusive with ``connection_string``, ``account_key``, and ``credential``."""

    max_concurrency: int = 8
    """Maximum parallel blob operations for grep/glob."""

    encoding: str = "utf-8"
    """Text encoding for blob content."""

    connection_string: Optional[str] = None
    """Full connection string (e.g., from Azure Portal or for Azurite).
    Mutually exclusive with ``account_key``, ``sas_token``, and ``credential``."""

    api_version: str = "2025-11-05"
    """Azure Storage API version string."""

    def __post_init__(self) -> None:
        """Validate that at most one explicit credential source is configured."""
        cred_sources = [
            ("connection_string", bool(self.connection_string)),
            ("account_key", bool(self.account_key)),
            ("sas_token", bool(self.sas_token)),
            ("credential", self.credential is not None),
        ]
        active = [name for name, is_set in cred_sources if is_set]

        if len(active) > 1:
            raise ValueError(
                f"Only one authentication method may be set, got: {', '.join(active)}. "
                f"Choose one of: connection_string, account_key, sas_token, credential, "
                f"or omit all to use DefaultAzureCredential."
            )

        # connection_string is self-contained; all other paths need account_url
        if not self.connection_string and not self.account_url:
            raise ValueError("account_url is required unless connection_string is provided.")

"""Azure Blob Storage filesystem backend for [LangChain Deep Agents](https://github.com/langchain-ai/deepagents).

> **Deprecated since 0.5.0.** This package is no longer maintained. Its backend now ships
> first-party as `AzureBlobBackend` in
> [`langchain-azure-storage`](https://pypi.org/project/langchain-azure-storage/):
>
> ```bash
> pip install "langchain-azure-storage[deepagents]"
> ```
>
> The constructor API changed, so this is not a drop-in swap — see the
> [migration guide](https://github.com/oddrationale/deepagents-azure-blob-backend#migrating-to-langchain-azure-storage).
> Released versions stay installable, but this package supports only `deepagents<0.7.0`.

This package provides `AzureBlobBackend`, an implementation of the Deep Agents
`BackendProtocol` that uses Azure Blob Storage as its virtual filesystem.

## Quick start

```python
from deepagents import create_deep_agent
from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

config = AzureBlobConfig(
    account_url="https://<account>.blob.core.windows.net",
    container_name="agent-workspace",
    prefix="session-001/",
)
backend = AzureBlobBackend(config)
agent = create_deep_agent(backend=backend)
```

## Authentication

`AzureBlobConfig` supports five mutually exclusive authentication methods:

1. **Connection string** — ``AzureBlobConfig(connection_string="...")``
2. **Account key** — ``AzureBlobConfig(account_url="...", account_key="...")``
3. **SAS token** — ``AzureBlobConfig(account_url="...", sas_token="...")``
4. **Credential object** — ``AzureBlobConfig(account_url="...", credential=my_cred)``
5. **Default (AAD)** — ``AzureBlobConfig(account_url="...")`` (uses ``DefaultAzureCredential``)

See `AzureBlobConfig` for full details and `AzureBlobBackend` for the API.
"""

import warnings

from .backend import AzureBlobBackend
from .config import AzureBlobConfig

_DEPRECATION_MESSAGE = (
    "deepagents-azure-blob-backend is deprecated and will receive no further updates. "
    "Its Azure Blob Storage backend now ships first-party as "
    "langchain_azure_storage.deepagents.AzureBlobBackend — install "
    "'langchain-azure-storage[deepagents]'. The constructor API changed, so this is not a "
    "drop-in swap: see "
    "https://github.com/oddrationale/deepagents-azure-blob-backend#migrating-to-langchain-azure-storage"
)

warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)

__all__ = ["AzureBlobBackend", "AzureBlobConfig"]

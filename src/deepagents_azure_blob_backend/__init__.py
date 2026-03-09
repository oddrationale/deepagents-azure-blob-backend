"""Azure Blob Storage filesystem backend for [LangChain Deep Agents](https://github.com/langchain-ai/deepagents).

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

from .backend import AzureBlobBackend
from .config import AzureBlobConfig

__all__ = ["AzureBlobBackend", "AzureBlobConfig"]

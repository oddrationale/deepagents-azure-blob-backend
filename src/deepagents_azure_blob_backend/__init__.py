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

See `AzureBlobConfig` for all available configuration options and
`AzureBlobBackend` for the full API.
"""

from .backend import AzureBlobBackend
from .config import AzureBlobConfig

__all__ = ["AzureBlobBackend", "AzureBlobConfig"]

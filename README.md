# deepagents-azure-blob-backend

[![CI](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/oddrationale/deepagents-azure-blob-backend/graph/badge.svg)](https://codecov.io/gh/oddrationale/deepagents-azure-blob-backend)

Azure Blob Storage filesystem backend for [LangChain Deep Agents](https://github.com/langchain-ai/deepagents).

Deep Agents exposes a `BackendProtocol` — a pluggable interface for file operations (`read`, `write`, `edit`, `ls`, `glob`, `grep`) that the agent uses as its virtual filesystem. This package provides a production-ready implementation backed by Azure Blob Storage.

## Installation

```bash
pip install deepagents-azure-blob-backend
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add deepagents-azure-blob-backend
```

## Quick Start

```python
import asyncio
from deepagents import create_deep_agent
from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

async def main():
    config = AzureBlobConfig(
        account_url="https://<your-account>.blob.core.windows.net",
        container_name="agent-workspace",
        prefix="session-001/",
    )
    backend = AzureBlobBackend(config)

    agent = create_deep_agent(backend=backend)

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Create a hello world script at /hello.py"}]},
    )
    print(result["messages"][-1].content)
    await backend.close()

asyncio.run(main())
```

## Configuration

```python
from deepagents_azure_blob_backend import AzureBlobConfig

config = AzureBlobConfig(
    account_url="https://<account>.blob.core.windows.net",
    container_name="my-container",
    prefix="agent-workspace/",     # Namespace isolation for multi-agent setups
    credential=None,               # None → DefaultAzureCredential()
    max_concurrency=8,             # Parallel blob ops for grep/glob
    encoding="utf-8",
    connection_string=None,        # Override for Azurite / testing
)
```

### Authentication

By default, `DefaultAzureCredential` is used, which supports:

- **Local development:** `az login`, environment variables
- **Azure Container Apps:** Managed identity
- **GitHub Actions:** Workload identity federation (OIDC)

For local development with [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite), use a connection string:

```python
config = AzureBlobConfig(
    container_name="test",
    connection_string="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;...",
)
```

## Supported Operations

All methods from `BackendProtocol`:

| Method | Async | Description |
|--------|-------|-------------|
| `ls_info(path)` | `als_info` | List directory with synthesized subdirectories |
| `read(path, offset, limit)` | `aread` | Read file with line numbers |
| `write(path, content)` | `awrite` | Create new file (errors if exists) |
| `edit(path, old, new)` | `aedit` | String replacement editing |
| `glob_info(pattern, path)` | `aglob_info` | Glob pattern file matching |
| `grep_raw(pattern, path, glob)` | `agrep_raw` | Literal text search across files |
| `upload_files(files)` | `aupload_files` | Batch binary upload |
| `download_files(paths)` | `adownload_files` | Batch binary download |

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run unit tests
uv run pytest tests/test_backend_unit.py -v

# Run integration tests (requires Azurite)
docker run -p 10000:10000 mcr.microsoft.com/azure-storage/azurite
uv run pytest tests/test_backend_integration.py -v
```

## License

MIT

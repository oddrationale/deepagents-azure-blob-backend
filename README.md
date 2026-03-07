# deepagents-azure-blob-backend

[![CI](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/oddrationale/deepagents-azure-blob-backend/graph/badge.svg)](https://codecov.io/gh/oddrationale/deepagents-azure-blob-backend)
[![PyPI Version](https://img.shields.io/pypi/v/deepagents-azure-blob-backend.svg)](https://pypi.python.org/pypi/deepagents-azure-blob-backend)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/deepagents-azure-blob-backend.svg)](https://pypi.python.org/pypi/deepagents-azure-blob-backend)
[![API Docs](https://img.shields.io/badge/docs-API%20reference-brightgreen)](https://oddrationale.github.io/deepagents-azure-blob-backend)
[![autofix.ci: yes](https://img.shields.io/badge/autofix.ci-yes-success?logo=data:image/svg+xml;base64,PHN2ZyBmaWxsPSIjZmZmIiB2aWV3Qm94PSIwIDAgMTI4IDEyOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCB0cmFuc2Zvcm09InNjYWxlKDAuMDYxLC0wLjA2MSkgdHJhbnNsYXRlKC0yNTAsLTE3NTApIiBkPSJNMTMyNSAtMzQwcS0xMTUgMCAtMTY0LjUgMzIuNXQtNDkuNSAxMTQuNXEwIDMyIDUgNzAuNXQxMC41IDcyLjV0NS41IDU0djIyMHEtMzQgLTkgLTY5LjUgLTE0dC03MS41IC01cS0xMzYgMCAtMjUxLjUgNjJ0LTE5MSAxNjl0LTkyLjUgMjQxcS05MCAxMjAgLTkwIDI2NnEwIDEwOCA0OC41IDIwMC41dDEzMiAxNTUuNXQxODguNSA4MXExNSA5OSAxMDAuNSAxODAuNXQyMTcgMTMwLjV0MjgyLjUgNDlxMTM2IDAgMjU2LjUgLTQ2IHQyMDkgLTEyNy41dDEyOC41IC0xODkuNXExNDkgLTgyIDIyNyAtMjEzLjV0NzggLTI5OS41cTAgLTEzNiAtNTggLTI0NnQtMTY1LjUgLTE4NC41dC0yNTYuNSAtMTAzLjVsLTI0MyAtMzAwdi01MnEwIC0yNyAzLjUgLTU2LjV0Ni41IC01Ny41dDMgLTUycTAgLTg1IC00MS41IC0xMTguNXQtMTU3LjUgLTMzLjV6TTEzMjUgLTI2MHE3NyAwIDk4IDE0LjV0MjEgNTcuNXEwIDI5IC0zIDY4dC02LjUgNzN0LTMuNSA0OHY2NGwyMDcgMjQ5IHEtMzEgMCAtNjAgNS41dC01NCAxMi41bC0xMDQgLTEyM3EtMSAzNCAtMiA2My41dC0xIDU0LjVxMCA2OSA5IDEyM2wzMSAyMDBsLTExNSAtMjhsLTQ2IC0yNzFsLTIwNSAyMjZxLTE5IC0xNSAtNDMgLTI4LjV0LTU1IC0yNi41bDIxOSAtMjQydi0yNzZxMCAtMjAgLTUuNSAtNjB0LTEwLjUgLTc5dC01IC01OHEwIC00MCAzMCAtNTMuNXQxMDQgLTEzLjV6TTEyNjIgNjE2cS0xMTkgMCAtMjI5LjUgMzQuNXQtMTkzLjUgOTYuNWw0OCA2NCBxNzMgLTU1IDE3MC41IC04NXQyMDQuNSAtMzBxMTM3IDAgMjQ5IDQ1LjV0MTc5IDEyMXQ2NyAxNjUuNWg4MHEwIC0xMTQgLTc3LjUgLTIwNy41dC0yMDggLTE0OXQtMjg5LjUgLTU1LjV6TTgwMyA1OTVxODAgMCAxNDkgMjkuNXQxMDggNzIuNWwyMjEgLTY3bDMwOSA4NnE0NyAtMzIgMTA0LjUgLTUwdDExNy41IC0xOHE5MSAwIDE2NSAzOHQxMTguNSAxMDMuNXQ0NC41IDE0Ni41cTAgNzYgLTM0LjUgMTQ5dC05NS41IDEzNHQtMTQzIDk5IHEtMzcgMTA3IC0xMTUuNSAxODMuNXQtMTg2IDExNy41dC0yMzAuNSA0MXEtMTAzIDAgLTE5Ny41IC0yNnQtMTY5IC03Mi41dC0xMTcuNSAtMTA4dC00MyAtMTMxLjVxMCAtMzQgMTQuNSAtNjIuNXQ0MC41IC01MC41bC01NSAtNTlxLTM0IDI5IC01NCA2NS41dC0yNSA4MS41cS04MSAtMTggLTE0NSAtNzB0LTEwMSAtMTI1LjV0LTM3IC0xNTguNXEwIC0xMDIgNDguNSAtMTgwLjV0MTI5LjUgLTEyM3QxNzkgLTQ0LjV6Ii8+PC9zdmc+)](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/autofix.yml)

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

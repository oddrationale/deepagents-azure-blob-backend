# deepagents-azure-blob-backend

[![CI](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/oddrationale/deepagents-azure-blob-backend/graph/badge.svg)](https://codecov.io/gh/oddrationale/deepagents-azure-blob-backend)
[![PyPI Version](https://img.shields.io/pypi/v/deepagents-azure-blob-backend.svg)](https://pypi.python.org/pypi/deepagents-azure-blob-backend)
[![PyPI Downloads](https://img.shields.io/pypi/dm/deepagents-azure-blob-backend.svg)](https://pypistats.org/packages/deepagents-azure-blob-backend)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/deepagents-azure-blob-backend.svg)](https://pypi.python.org/pypi/deepagents-azure-blob-backend)
[![API Docs](https://img.shields.io/badge/docs-API%20reference-brightgreen)](https://oddrationale.github.io/deepagents-azure-blob-backend)
[![autofix.ci](https://img.shields.io/badge/autofix.ci-enabled-success)](https://github.com/oddrationale/deepagents-azure-blob-backend/actions/workflows/autofix.ci.yml)

> [!WARNING]
> **This package is deprecated and no longer maintained.**
>
> Its Azure Blob Storage backend now ships first-party in [`langchain-azure-storage`](https://pypi.org/project/langchain-azure-storage/), maintained by LangChain and Microsoft in [langchain-ai/langchain-azure](https://github.com/langchain-ai/langchain-azure):
>
> ```bash
> pip install "langchain-azure-storage[deepagents]"
> ```
>
> The constructor API changed during upstream review, so this is not a drop-in swap — see [Migrating to langchain-azure-storage](#migrating-to-langchain-azure-storage) below.
>
> Existing releases stay installable and nothing is yanked, but `0.5.0` is the last one. It supports only `deepagents<0.7.0`; for `deepagents>=0.7.1`, use `langchain-azure-storage`.

Azure Blob Storage filesystem backend for [LangChain Deep Agents](https://github.com/langchain-ai/deepagents).

Deep Agents exposes a `BackendProtocol` — a pluggable interface for file operations (`read`, `write`, `edit`, `ls`, `glob`, `grep`) that the agent uses as its virtual filesystem. This package provides an Azure Blob Storage implementation of that interface.

## Migrating to langchain-azure-storage

```bash
pip uninstall deepagents-azure-blob-backend
pip install "langchain-azure-storage[deepagents]"
```

The successor drops the `AzureBlobConfig` dataclass and takes its arguments directly on the constructor. Credentials are Azure SDK credential objects rather than raw key or token strings:

```python
# Before
from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

backend = AzureBlobBackend(
    AzureBlobConfig(
        account_url="https://<account>.blob.core.windows.net",
        container_name="agent-workspace",
        prefix="session-001/",
    )
)

# After
from langchain_azure_storage.deepagents import AzureBlobBackend

backend = AzureBlobBackend(
    "https://<account>.blob.core.windows.net",
    "agent-workspace",
    prefix="session-001/",
)
```

| `AzureBlobConfig` field | Replacement |
|---|---|
| `account_url`, `container_name` | Positional arguments to `AzureBlobBackend(...)` |
| `prefix` | Keyword argument `prefix=` |
| `credential=<azure credential>` | Keyword argument `credential=` (`TokenCredential`, `AsyncTokenCredential`, or `AzureSasCredential`) |
| `connection_string="..."` | `AzureBlobBackend.from_connection_string(connection_string, container_name, prefix=...)` |
| `sas_token="sv=..."` | `credential=AzureSasCredential("sv=...")` (from `azure.core.credentials`) |
| `account_key="..."` | No direct equivalent — use `from_connection_string` (a connection string carries `AccountKey`) or a SAS credential |
| *(omit all credentials)* | Unchanged — `DefaultAzureCredential` is still the default |
| `max_concurrency`, `encoding`, `api_version` | Not exposed; the successor manages concurrency and encoding internally |

The successor also requires `deepagents>=0.7.1`, where `write` overwrites an existing file instead of erroring and `delete`/`adelete` are part of `BackendProtocol`. Python 3.11+ is required for the `deepagents` extra.

Further reading: [backend integrations](https://docs.langchain.com/oss/python/integrations/backends) · [design proposal and behavior notes](https://github.com/langchain-ai/langchain-azure/blob/main/libs/azure-storage/proposals/deepagents_backend.md) · [upstream PR](https://github.com/langchain-ai/langchain-azure/pull/783)

## Installation

```bash
pip install deepagents-azure-blob-backend
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add deepagents-azure-blob-backend
```

This package requires `deepagents>=0.6.1,<0.7.0`, where `BackendProtocol` exposes structured `ls`, `glob`, and `grep` result types. It does not support the `BackendProtocol` changes in `deepagents` 0.7.0 — see [Migrating to langchain-azure-storage](#migrating-to-langchain-azure-storage).

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
    prefix="agent-workspace/",  # Namespace isolation for multi-agent setups
    max_concurrency=8,  # Parallel blob ops for grep/glob
    encoding="utf-8",
)
```

### Authentication

`AzureBlobConfig` supports five mutually exclusive authentication methods. Set at most one credential source — if none is provided, `DefaultAzureCredential` is used automatically. `account_url` is required for all methods except connection string:

```python
# 1. Connection string (e.g., Azurite or Azure Portal)
config = AzureBlobConfig(
    container_name="test",
    connection_string="UseDevelopmentStorage=true",
)

# 2. Account key
config = AzureBlobConfig(
    account_url="https://<account>.blob.core.windows.net",
    container_name="my-container",
    account_key="your-storage-account-key",
)

# 3. SAS token
config = AzureBlobConfig(
    account_url="https://<account>.blob.core.windows.net",
    container_name="my-container",
    sas_token="sv=2021-06-08&ss=b&srt=co&sp=rwdlacitfx&se=...",
)

# 4. Credential object (any Azure credential)
from azure.identity.aio import ClientSecretCredential

config = AzureBlobConfig(
    account_url="https://<account>.blob.core.windows.net",
    container_name="my-container",
    credential=ClientSecretCredential(tenant_id, client_id, client_secret),
)

# 5. Default (AAD) — omit all credential fields
config = AzureBlobConfig(
    account_url="https://<account>.blob.core.windows.net",
    container_name="my-container",
)
```

The default path uses `DefaultAzureCredential`, which supports `az login`, managed identity, workload identity federation (OIDC), and environment variables.

## Supported Operations

All methods from `BackendProtocol`:

| Method | Async | Description |
|--------|-------|-------------|
| `ls(path)` | `als` | List directory with synthesized subdirectories |
| `read(path, offset, limit)` | `aread` | Read file with line numbers |
| `write(path, content)` | `awrite` | Create new file (errors if exists) |
| `edit(path, old, new)` | `aedit` | String replacement editing |
| `glob(pattern, path)` | `aglob` | Glob pattern file matching |
| `grep(pattern, path, glob)` | `agrep` | Literal text search across files |
| `upload_files(files)` | `aupload_files` | Batch binary upload |
| `download_files(paths)` | `adownload_files` | Batch binary download |

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run unit tests
uv run pytest tests/unit_tests -v

# Run integration tests (requires Azurite)
docker run -p 10000:10000 mcr.microsoft.com/azure-storage/azurite azurite-blob --skipApiVersionCheck --blobHost 0.0.0.0
uv run pytest tests/integration_tests -v

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run ty check
```

See the [examples/](examples/) folder for runnable scripts with setup instructions.

## License

MIT

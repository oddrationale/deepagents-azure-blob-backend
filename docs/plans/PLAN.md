# PLAN.md — `deepagents-azure-blob-backend`

## Project Summary

An open-source Python package that implements an Azure Blob Storage filesystem backend for [LangChain Deep Agents](https://github.com/langchain-ai/deepagents). Deep Agents exposes a `BackendProtocol` — a pluggable interface for file operations (`read`, `write`, `edit`, `ls`, `glob`, `grep`) that the agent uses as its virtual filesystem. This package provides a production-ready implementation backed by Azure Blob Storage.

**PyPI package name:** `deepagents-azure-blob-backend`
**Import name:** `deepagents_azure_blob_backend`
**GitHub repo name:** `deepagents-azure-blob-backend`
**License:** MIT

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Async client | `azure.storage.blob.aio.BlobServiceClient` | Native async, LangGraph is async-first |
| Sync methods | Thin wrappers over async via `asyncio.run()` | Avoid duplicating logic |
| Authentication | `DefaultAzureCredential` only (for now) | Covers local dev, ACA managed identity, GitHub Actions OIDC; other auth methods can be added later |
| Content storage | Raw UTF-8 text in blob body | Human-readable, interoperable with Azure Portal/AzCopy; `created_at`/`modified_at` stored as blob metadata |
| Directory support | No directory marker blobs | Matches S3Backend approach in `deepagents-backends`; directories are synthesized on-the-fly from prefix scans |
| Type checking | `ty` instead of mypy | 10–100x faster; from Astral (same team as uv/ruff); note: launched March 2025, still pre-1.0 |
| Integration testing | Azurite in GitHub Actions service container | Official Microsoft emulator, zero cost, no real Azure account needed in CI |
| Python support | 3.9+ | Matches `deepagents` and `azure-storage-blob` minimum |

---

## Reference Implementations

Study these before writing any code:

- **`deepagents` built-in `StateBackend`** — simplest backend, shows expected return shapes for all protocol methods
- **`deepagents-backends` by DiTo97** (`pip install deepagents-backends`) — the only existing community backend; provides `S3Backend` and `PostgresBackend`. Use as primary structural reference, especially for async patterns and test setup
- **Official LangChain docs S3 sketch** — https://docs.langchain.com/oss/python/deepagents/backends

---

## Protocol to Implement

All methods from `deepagents.backends.protocol.BackendProtocol`:

| Method | Async variant | Description |
|--------|--------------|-------------|
| `ls_info(path)` | `als_info` | List directory contents; synthesize dir entries from blob prefix scan |
| `read(file_path, offset, limit)` | `aread` | Download blob, decode UTF-8, return numbered lines with offset/limit |
| `write(file_path, content)` | `awrite` | Upload blob with `overwrite=True`; set `created_at`/`modified_at` as metadata |
| `edit(file_path, old_str, new_str)` | `aedit` | Read → string replace → write; return `EditResult` |
| `glob_info(pattern, path)` | `aglob_info` | List all blobs under path, apply `fnmatch` filter, return `FileInfo` list |
| `grep_raw(pattern, path, glob)` | `agrep_raw` | Download matching blobs, run `re.search` per line, return `GrepMatch` list |
| `upload_files(files)` | `aupload_files` | Batch upload raw bytes |
| `download_files(paths)` | `adownload_files` | Batch download as bytes |

**Confirm before implementing:**
- Whether `files_update` must return `None` for external backends (check `StateBackend` source)
- Exact fields required on `FileInfo`, `WriteResult`, `EditResult`, `GrepMatch`
- Whether both sync and async are required or async-only is acceptable

---

## The Flat Namespace Problem

Blob Storage has no real directories — only blob keys with `/` in their names. This affects `ls_info` specifically:

- A blob at `agent-workspace/src/utils.py` must appear as file `utils.py` under the "directory" `/src/`
- `ls_info("/src/")` must also return synthesized directory entries for any nested sub-prefixes
- There are no empty directories — if all blobs under a prefix are deleted, that "directory" ceases to exist (same behavior as `S3Backend`)
- `move` is O(n): copy all blobs under source prefix + delete originals

---

## Content Model

**Blob body:** raw UTF-8 text (the file content as a string)

**Blob metadata tags:**
```
created_at: 2025-01-01T00:00:00Z
modified_at: 2025-01-01T00:00:00Z
```

On `read`, reconstruct the line array by splitting on `\n`. Use `deepagents.backends.utils.create_file_data` for building `FileInfo`-compatible structures where needed.

---

## `AzureBlobConfig`

```python
@dataclass
class AzureBlobConfig:
    account_url: str           # https://<account>.blob.core.windows.net
    container_name: str        # Target blob container
    prefix: str = ""           # Key namespace within container (supports multi-agent isolation)
    credential: Any = None     # None → DefaultAzureCredential(); injectable for testing
    max_concurrency: int = 8   # Parallel blob ops for grep/glob
    encoding: str = "utf-8"
    connection_string: str | None = None  # Override for Azurite / testing
```

---

## Package Structure

```
deepagents-azure-blob-backend/
├── src/
│   └── deepagents_azure_blob_backend/
│       ├── __init__.py          # Exports: AzureBlobBackend, AzureBlobConfig
│       ├── backend.py           # Main AzureBlobBackend class
│       ├── config.py            # AzureBlobConfig
│       ├── _path.py             # Path normalization utilities
│       └── _utils.py            # FileInfo builders, content helpers
├── tests/
│   ├── conftest.py              # Azurite fixture (session-scoped), container creation
│   ├── test_backend_unit.py     # Unit tests (mocked, no I/O)
│   └── test_backend_integration.py  # Integration tests (requires Azurite)
├── examples/
│   ├── basic_agent.py
│   └── composite_with_memories.py
├── .github/
│   └── workflows/
│       ├── ci.yml               # Test + lint on every push/PR
│       └── publish.yml          # Publish to PyPI on version tag
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── SECURITY.md
```

---

## Repository Initialization

Bootstrap with uv's library template, which sets up the `src/` layout, `py.typed` marker, and `uv_build` build system automatically:

```bash
uv init --lib deepagents-azure-blob-backend
cd deepagents-azure-blob-backend
uv add azure-storage-blob azure-identity deepagents
uv add --dev pytest pytest-asyncio pytest-cov ruff ty
```

## `pyproject.toml` (key sections)

```toml
[build-system]
requires = ["uv_build>=0.10.7,<0.11.0"]
build-backend = "uv_build"

[project]
name = "deepagents-azure-blob-backend"
version = "0.1.0"
description = "Azure Blob Storage filesystem backend for LangChain Deep Agents"
requires-python = ">=3.9"
license = { text = "MIT" }
keywords = ["langchain", "deepagents", "azure", "blob-storage", "agent", "backend", "llm"]
dependencies = [
    "deepagents>=0.4.0",
    "azure-storage-blob>=12.0.0",
    "azure-identity>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-asyncio>=0.21", "pytest-cov", "ruff", "ty"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = ["unit: no I/O", "integration: requires Azurite"]
```

---

## GitHub Actions — CI (`ci.yml`)

```yaml
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      azurite:
        image: mcr.microsoft.com/azure-storage/azurite
        ports:
          - 10000:10000
        options: >-
          --health-cmd "nc -z localhost 10000"
          --health-interval 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest --cov -m "unit or integration"
        env:
          AZURE_STORAGE_CONNECTION_STRING: "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
      - run: ruff check .
      - run: uvx ty check
```

---

## GitHub Actions — Publish (`publish.yml`)

Uses PyPI Trusted Publishing (OIDC) — no API token secrets required.

```yaml
on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

## Integration Test Setup (conftest.py)

```python
import os
import pytest
from azure.storage.blob.aio import BlobServiceClient

AZURITE_CONN_STR = os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)
TEST_CONTAINER = "test-deepagents"

@pytest.fixture(scope="session")
async def blob_container():
    async with BlobServiceClient.from_connection_string(AZURITE_CONN_STR) as client:
        await client.create_container(TEST_CONTAINER)
        yield TEST_CONTAINER

@pytest.fixture
async def backend(blob_container):
    from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig
    config = AzureBlobConfig(
        account_url="",  # unused when connection_string is set
        container_name=blob_container,
        connection_string=AZURITE_CONN_STR,
        prefix="test-run/",
    )
    backend = AzureBlobBackend(config)
    yield backend
    await backend.close()
```

---

## Testing Strategy

The `deepagents` repo has **no reusable conformance test suite** for backends — tests are all backend-specific and not parametrizable. You must write your own, but the upstream tests are useful as a behavioral reference.

**Upstream files to study before writing tests:**
- `libs/deepagents/tests/unit_tests/backends/test_composite_backend.py` — best reference; covers `ls_info`, `read`, `write`, `edit`, `glob_info`, `grep_raw` end-to-end with assertions on return shapes
- `libs/deepagents/tests/unit_tests/backends/test_store_backend_async.py` — async pattern reference; shows how to mock a LangGraph store and assert on `WriteResult`/`EditResult` fields
- `libs/deepagents/tests/unit_tests/test_file_system_tools.py` — tests the middleware tool layer (not the backend directly), useful for understanding expected behavior from the agent's perspective

**What your `test_backend_integration.py` should cover** (mirror the contract implied by the upstream tests):

| Method | Key assertions |
|--------|---------------|
| `write` / `awrite` | Returns `WriteResult(error=None, path=<path>, files_update=None)` |
| `read` / `aread` | Returns line-numbered string; respects `offset` and `limit` |
| `ls_info` / `als_info` | Returns `[FileInfo]`; directories have trailing `/` and `is_dir=True`; non-existent path returns `[]` |
| `edit` / `aedit` | Returns `EditResult(error=None, ...)`; fails if `old_str` not unique |
| `glob_info` / `aglob_info` | Supports `*`, `**`, `?` patterns |
| `grep_raw` / `agrep_raw` | Returns `[GrepMatch]` with correct `path`, `line`, `text` |
| `upload_files` / `download_files` | Round-trip bytes fidelity |

Also add a `test_backend_unit.py` that mocks the Azure SDK client (`AsyncMock` on `BlobServiceClient`) to cover error paths (blob not found, network failure, encoding errors) without needing Azurite.

---

## Publishing to PyPI

1. Publish `v0.0.1` manually first to claim the `deepagents-azure-blob-backend` namespace on PyPI
2. In PyPI project settings → Publishing → add GitHub as a Trusted Publisher (set repo, workflow filename `publish.yml`, environment `pypi`)
3. All subsequent releases via `git tag v0.1.0 && git push --tags`

Test on TestPyPI first:
```bash
python -m build
twine upload --repository testpypi dist/*
pip install -i https://test.pypi.org/simple/ deepagents-azure-blob-backend
```

---

## Open Questions (resolve by reading source before coding)

1. Does `BackendProtocol` require both sync and async, or async-only?
2. What is the exact signature and required fields of `FileInfo`, `WriteResult`, `EditResult`, `GrepMatch`?
3. What does `ls_info` return for a non-existent path — empty list or error string?
4. Must `files_update` be `None` in `WriteResult`/`EditResult` for external backends?
5. Does `CompositeBackend` inject a runtime context into the backend? If so, does your backend need to accept it?
6. Does `deepagents` have a preferred naming convention for community backends (check `CONTRIBUTING.md`)?
7. ~~Is there an official backend conformance test suite in the `deepagents` repo?~~ **Confirmed: No.** See Testing Strategy section below.

---

## Launch Checklist

- [ ] Claim `deepagents-azure-blob-backend` on PyPI (publish v0.0.1)
- [ ] Set up PyPI Trusted Publisher in project settings
- [ ] Set GitHub repo topics: `langchain`, `deepagents`, `azure`, `azure-blob-storage`, `llm`, `ai-agents`, `python`
- [ ] Open discussion/issue on `langchain-ai/deepagents` announcing the package
- [ ] Submit PR to Deep Agents docs to add a "Community Backends" section
- [ ] Post on LangChain Forum (forum.langchain.com)

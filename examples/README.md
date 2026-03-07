# Examples

Example scripts showing how to use `deepagents-azure-blob-backend` with Deep Agents.

## Setup

The examples use [uv](https://docs.astral.sh/uv/) for dependency management. The `pyproject.toml` in this directory references the parent package as a path dependency, so changes to the backend are picked up automatically.

```bash
cd examples/
uv sync
```

## Configuration

Before running any example, configure Azure Blob Storage credentials using one of:

- **Connection string** (e.g. for [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite)):
  ```bash
  export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;..."
  ```
- **Default credentials** (`az login`, managed identity, etc.) — no env vars needed.

You also need an `ANTHROPIC_API_KEY` set for the LLM calls.

Edit the `account_url` and `container_name` values in each script to match your environment.

## Running

```bash
# From the examples/ directory
uv run python basic_agent.py
uv run python composite_with_memories.py
```

## What each example does

| File | Description |
|------|-------------|
| `basic_agent.py` | Minimal setup — creates a Deep Agent with an Azure Blob backend using the default model. |
| `composite_with_memories.py` | Same pattern but with an explicit `ChatAnthropic` model to show how to customize the LLM. |

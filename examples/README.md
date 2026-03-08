# Examples

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed
- [Docker](https://docs.docker.com/get-docker/) installed (for Azurite)
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

### 1. Start Azurite (local Azure Storage emulator)

```bash
docker run -d --name azurite \
  -p 10000:10000 -p 10001:10001 -p 10002:10002 \
  mcr.microsoft.com/azure-storage/azurite \
  azurite --skipApiVersionCheck -l /data --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0
```

### 2. Configure environment variables

Create a `.env` file in this directory:

```env
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
```

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Required. Your Anthropic API key. |
| `AZURE_STORAGE_CONNECTION_STRING` | Use a connection string for auth (e.g. Azurite). |
| `AZURE_STORAGE_ACCOUNT_URL` | Use an account URL (required unless using a connection string). |
| `AZURE_STORAGE_ACCOUNT_KEY` | Authenticate with a storage account key. |
| `AZURE_STORAGE_SAS_TOKEN` | Authenticate with a SAS token. |

Set `AZURE_STORAGE_CONNECTION_STRING` **or** `AZURE_STORAGE_ACCOUNT_URL` with one of the credential variables. If a connection string is set, other credential variables are ignored. If no credential variable is set, `DefaultAzureCredential` is used automatically.

The `.env` file is gitignored and will not be committed.

## Running the examples

Each example uses [PEP 723 inline script metadata](https://peps.python.org/pep-0723/), so uv automatically installs dependencies — no separate install step needed.

### Basic agent

A minimal example that creates a Deep Agent backed by Azure Blob Storage.

```bash
cd examples
uv run --env-file .env basic_agent.py
```

### Composite agent with memory and subagents

Demonstrates loading project conventions from an `AGENTS.md` memory file and delegating work to specialized subagents (a coder and a tester).

```bash
cd examples
uv run --env-file .env composite_with_memories.py
```

## Using Azure Storage Explorer

To browse blobs created by the examples:

1. Install [Azure Storage Explorer](https://azure.microsoft.com/products/storage/storage-explorer)
2. Click the **Connect** (plug) icon
3. Select **Local storage emulator**
4. Use the default connection settings and click **Connect**
5. Browse the `agent-workspace` container under **Local & Attached > Storage Accounts > devstoreaccount1 > Blob Containers**

## Production usage

To run against real Azure Blob Storage instead of Azurite, replace the connection string with an account URL in your `.env`:

```env
AZURE_STORAGE_ACCOUNT_URL=https://<your-account>.blob.core.windows.net
```

Ensure `DefaultAzureCredential` is configured (e.g. `az login`, managed identity, or environment variables).

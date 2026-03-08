# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "deepagents",
#     "deepagents-azure-blob-backend",
#     "langchain-anthropic",
# ]
# ///
"""Basic example: using AzureBlobBackend with a Deep Agent.

Run with:
    uv run --env-file .env basic_agent.py

Environment variables:
    AZURE_STORAGE_CONNECTION_STRING  — Connection string (e.g. Azurite). Overrides all others.
    AZURE_STORAGE_ACCOUNT_URL        — Account URL (required unless using connection string).
    AZURE_STORAGE_ACCOUNT_KEY        — Storage account key.
    AZURE_STORAGE_SAS_TOKEN          — SAS token.
    ANTHROPIC_API_KEY                — Required for the default Anthropic model.

    Set AZURE_STORAGE_CONNECTION_STRING *or* AZURE_STORAGE_ACCOUNT_URL with
    at most one of AZURE_STORAGE_ACCOUNT_KEY / AZURE_STORAGE_SAS_TOKEN.
    If no credential env var is set, DefaultAzureCredential is used.
"""

import asyncio
import os

from azure.storage.blob import BlobServiceClient
from deepagents import create_deep_agent

from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

CONTAINER_NAME = "agent-workspace"


def build_config() -> AzureBlobConfig:
    """Build config from environment variables."""
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL", "")
    account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    sas_token = os.environ.get("AZURE_STORAGE_SAS_TOKEN")

    if connection_string:
        return AzureBlobConfig(
            connection_string=connection_string,
            container_name=CONTAINER_NAME,
            prefix="session-001/",
        )
    if not account_url:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL")

    # SAS token takes priority over account key if both are set
    return AzureBlobConfig(
        account_url=account_url,
        container_name=CONTAINER_NAME,
        prefix="session-001/",
        account_key=account_key if not sas_token else None,
        sas_token=sas_token,
    )


def _resolve_sync_credential(config: AzureBlobConfig):
    """Return the credential to use with the sync BlobServiceClient."""
    if config.account_key:
        return config.account_key
    if config.sas_token:
        from azure.core.credentials import AzureSasCredential

        return AzureSasCredential(config.sas_token.lstrip("?"))
    if config.credential is not None:
        return config.credential
    # Fall back to DefaultAzureCredential for AAD-based auth
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def ensure_container(config: AzureBlobConfig) -> None:
    """Create the blob container if it doesn't already exist."""
    client = None
    try:
        if config.connection_string:
            client = BlobServiceClient.from_connection_string(
                conn_str=config.connection_string,
                api_version=config.api_version,
            )
        else:
            client = BlobServiceClient(
                account_url=config.account_url,
                credential=_resolve_sync_credential(config),
                api_version=config.api_version,
            )

        container = client.get_container_client(config.container_name)
        if not container.exists():
            container.create_container()
            print(f"Created container '{config.container_name}'")
    finally:
        if client is not None:
            client.close()


async def main():
    config = build_config()
    ensure_container(config)

    backend = AzureBlobBackend(config)
    agent = create_deep_agent(backend=backend)

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Create a Python hello world script at /hello.py"}]},
    )

    print(result["messages"][-1].content)

    await backend.close()


if __name__ == "__main__":
    asyncio.run(main())

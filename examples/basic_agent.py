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
    AZURE_STORAGE_CONNECTION_STRING  — Use a connection string (e.g. Azurite).
    AZURE_STORAGE_ACCOUNT_URL        — Use an account URL with DefaultAzureCredential.
    ANTHROPIC_API_KEY                — Required for the default Anthropic model.

    Set either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL. If both are set, the connection string takes priority.
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
    account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")

    if connection_string:
        return AzureBlobConfig(
            connection_string=connection_string,
            container_name=CONTAINER_NAME,
            prefix="session-001/",
        )
    elif account_url:
        return AzureBlobConfig(
            account_url=account_url,
            container_name=CONTAINER_NAME,
            prefix="session-001/",
        )
    else:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL")


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
                credential=config.credential,
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

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "deepagents",
#     "deepagents-azure-blob-backend",
#     "langchain-anthropic",
# ]
# ///
"""Example: composite agent with memory and subagents.

Demonstrates:
  - Loading memory from AGENTS.md files via the `memory` parameter
  - Defining specialized subagents that the main agent can delegate to
  - Using a shared Azure Blob Storage backend across all agents

Run with:
    uv run --env-file .env composite_with_memories.py

Environment variables:
    AZURE_STORAGE_CONNECTION_STRING  — Use a connection string (e.g. Azurite).
    AZURE_STORAGE_ACCOUNT_URL        — Use an account URL with DefaultAzureCredential.
    ANTHROPIC_API_KEY                — Required for the default Anthropic model.

    Set either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL. If both are set, the connection string takes priority.
"""

import asyncio
import os

from azure.storage.blob import BlobServiceClient
from deepagents import SubAgent, create_deep_agent

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
            prefix="composite-demo/",
        )
    elif account_url:
        return AzureBlobConfig(
            account_url=account_url,
            container_name=CONTAINER_NAME,
            prefix="composite-demo/",
        )
    else:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL")


def ensure_container(config: AzureBlobConfig) -> None:
    """Create the blob container if it doesn't already exist."""
    client: BlobServiceClient | None = None
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

    # Seed an AGENTS.md memory file so the agent picks up project conventions
    await backend.awrite(
        ".deepagents/AGENTS.md",
        "# Project Conventions\n\n"
        "- Use snake_case for all Python identifiers\n"
        "- Include docstrings on every public function\n"
        "- Write pytest-style tests\n",
    )

    # Define specialized subagents
    subagents = [
        SubAgent(
            name="coder",
            description="Writes Python source code modules.",
            system_prompt=(
                "You are a Python developer. Write clean, well-documented code. "
                "Always include type hints and docstrings."
            ),
        ),
        SubAgent(
            name="tester",
            description="Writes pytest test files for existing code.",
            system_prompt=(
                "You are a test engineer. Read the source code and write comprehensive "
                "pytest tests. Cover edge cases and error conditions."
            ),
        ),
    ]

    # Create the main agent with memory and subagents
    agent = create_deep_agent(
        backend=backend,
        subagents=subagents,
        # Load project conventions from the AGENTS.md file
        memory=[".deepagents/AGENTS.md"],
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Create a Python module at /src/calculator.py with add, subtract, "
                        "multiply, and divide functions. Then write tests for it at "
                        "/tests/test_calculator.py."
                    ),
                }
            ]
        },
    )

    print(result["messages"][-1].content)

    await backend.close()


if __name__ == "__main__":
    asyncio.run(main())

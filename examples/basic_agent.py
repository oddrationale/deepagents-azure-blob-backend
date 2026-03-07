"""Basic example: using AzureBlobBackend with a Deep Agent.

Prerequisites:
    pip install deepagents deepagents-azure-blob-backend langchain-anthropic

    Either:
    - Set AZURE_STORAGE_CONNECTION_STRING for Azurite / connection string auth
    - Or ensure DefaultAzureCredential works (az login, managed identity, etc.)
"""

import asyncio

from deepagents import create_agent
from langchain_anthropic import ChatAnthropic

from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig


async def main():
    # Configure the Azure Blob Storage backend
    config = AzureBlobConfig(
        account_url="https://<your-account>.blob.core.windows.net",
        container_name="agent-workspace",
        prefix="session-001/",  # Isolate each agent session
    )
    backend = AzureBlobBackend(config)

    # Create a Deep Agent with the Azure backend
    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    agent = create_agent(model, backend=backend)

    # Run the agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Create a Python hello world script at /hello.py"}]},
    )

    print(result["messages"][-1].content)

    # Clean up
    await backend.close()


if __name__ == "__main__":
    asyncio.run(main())

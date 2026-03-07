"""Example: using AzureBlobBackend with a custom model.

This shows how to configure an AzureBlobBackend with a specific model
so agents can read/write files that persist in Azure Blob Storage.

Prerequisites:
    pip install deepagents deepagents-azure-blob-backend langchain-anthropic
"""

import asyncio

from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic

from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig


async def main():
    # Azure Blob backend for persistent file storage
    azure_config = AzureBlobConfig(
        account_url="https://<your-account>.blob.core.windows.net",
        container_name="agent-outputs",
        prefix="project-alpha/",
    )
    azure_backend = AzureBlobBackend(azure_config)

    # Create a Deep Agent with a specific model and the Azure backend
    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    agent = create_deep_agent(model=model, backend=azure_backend)

    # The agent can now read/write files that persist in Azure Blob Storage
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write a Python module at /src/calculator.py that implements "
                        "add, subtract, multiply, and divide functions."
                    ),
                }
            ]
        },
    )

    print(result["messages"][-1].content)

    await azure_backend.close()


if __name__ == "__main__":
    asyncio.run(main())

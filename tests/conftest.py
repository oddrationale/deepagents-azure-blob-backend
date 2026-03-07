"""Shared fixtures for tests."""

from __future__ import annotations

import os
import uuid

import pytest

from deepagents_azure_blob_backend import AzureBlobConfig

AZURITE_CONN_STR = os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
    "K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
)

TEST_CONTAINER = "test-deepagents"


@pytest.fixture(scope="session")
async def blob_container():
    """Create a test container in Azurite (session-scoped)."""
    from azure.core.exceptions import ResourceExistsError
    from azure.storage.blob.aio import BlobServiceClient

    async with BlobServiceClient.from_connection_string(
        AZURITE_CONN_STR, api_version=AzureBlobConfig.api_version
    ) as client:
        try:
            await client.create_container(TEST_CONTAINER)
        except ResourceExistsError:
            pass  # Container may already exist
        yield TEST_CONTAINER


@pytest.fixture
async def backend(blob_container):
    """Create a fresh AzureBlobBackend for each test with a unique prefix."""
    from deepagents_azure_blob_backend import AzureBlobBackend, AzureBlobConfig

    config = AzureBlobConfig(
        account_url="",  # unused when connection_string is set
        container_name=blob_container,
        connection_string=AZURITE_CONN_STR,
        prefix=f"test-{uuid.uuid4().hex[:8]}/",
    )
    b = AzureBlobBackend(config)
    yield b
    await b.close()

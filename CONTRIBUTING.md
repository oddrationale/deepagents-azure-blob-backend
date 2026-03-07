# Contributing

Contributions are welcome! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/oddrationale/deepagents-azure-blob-backend.git
cd deepagents-azure-blob-backend

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync --group dev
```

## Running Tests

### Unit tests (no external dependencies)

```bash
uv run pytest tests/test_backend_unit.py -v
```

### Integration tests (requires Azurite)

Start Azurite (Azure Storage emulator):

```bash
# Using Docker
docker run -p 10000:10000 mcr.microsoft.com/azure-storage/azurite

# Or install via npm
npm install -g azurite
azurite-blob --blobPort 10000
```

Run integration tests:

```bash
uv run pytest tests/test_backend_integration.py -v
```

## Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run ty check
```

## Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests and linting
5. Submit a pull request

Please ensure all tests pass and code follows the existing style.

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
docker run -p 10000:10000 mcr.microsoft.com/azure-storage/azurite azurite-blob --skipApiVersionCheck --blobHost 0.0.0.0

# Or install via npm
npm install -g azurite
azurite-blob --blobPort 10000 --skipApiVersionCheck
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

Please ensure all tests pass and code follows the existing style. An [autofix.ci](https://autofix.ci) bot will automatically fix lint and formatting issues on your PR.

## Releases

After a release PR is merged, `Release Please` will create the GitHub release and trigger the reusable publish workflow automatically.

If you need to run publishing manually after merge, open **Actions** → **Publish to PyPI** → **Run workflow**, then select the release tag (preferred) or `main` as the ref before starting the run.

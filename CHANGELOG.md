# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- Initial release of `deepagents-azure-blob-backend`
- `AzureBlobBackend` implementing `BackendProtocol` from `deepagents`
- `AzureBlobConfig` dataclass for configuration
- Full support for all `BackendProtocol` methods:
  - `ls_info` / `als_info` — directory listing with synthesized directories
  - `read` / `aread` — line-numbered file reading with offset/limit
  - `write` / `awrite` — file creation (errors if exists)
  - `edit` / `aedit` — string replacement editing
  - `glob_info` / `aglob_info` — glob pattern file matching
  - `grep_raw` / `agrep_raw` — literal text search with concurrent blob reads
  - `upload_files` / `aupload_files` — batch binary upload
  - `download_files` / `adownload_files` — batch binary download
- Native async implementation with sync wrappers
- `DefaultAzureCredential` support for production use
- Connection string support for Azurite/testing
- Prefix-based namespace isolation for multi-agent setups
- Unit and integration test suites
- CI with Azurite service container
- PyPI Trusted Publishing workflow

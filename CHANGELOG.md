# Changelog

## [0.2.2](https://github.com/oddrationale/deepagents-azure-blob-backend/compare/deepagents-azure-blob-backend-v0.2.1...deepagents-azure-blob-backend-v0.2.2) (2026-04-27)


### Features

* support Deep Agents 0.5 ReadResult API ([4a4c011](https://github.com/oddrationale/deepagents-azure-blob-backend/commit/4a4c01126a4f9bb2fe4d400c0696aad493766ef8))

## [0.2.1](https://github.com/oddrationale/deepagents-azure-blob-backend/compare/deepagents-azure-blob-backend-v0.2.0...deepagents-azure-blob-backend-v0.2.1) (2026-04-23)


### Bug Fixes

* isolate sync wrapper event loops from cached client ([#30](https://github.com/oddrationale/deepagents-azure-blob-backend/issues/30)) ([d01157a](https://github.com/oddrationale/deepagents-azure-blob-backend/commit/d01157a00a0ac29079d7d6dbf18434fca875c8be))
* remediate dependabot alerts ([#32](https://github.com/oddrationale/deepagents-azure-blob-backend/issues/32)) ([6fb2601](https://github.com/oddrationale/deepagents-azure-blob-backend/commit/6fb2601bb2aa3d7a008c0e6fe389325280f16e6c))

## [0.2.0](https://github.com/oddrationale/deepagents-azure-blob-backend/compare/deepagents-azure-blob-backend-v0.1.2...deepagents-azure-blob-backend-v0.2.0) (2026-03-09)


### ⚠ BREAKING CHANGES

* `AzureBlobConfig()` with no arguments now raises `ValueError` — `account_url` or `connection_string` is required.

### Features

* add first-class SAS token and account key authentication ([#17](https://github.com/oddrationale/deepagents-azure-blob-backend/issues/17)) ([cd19886](https://github.com/oddrationale/deepagents-azure-blob-backend/commit/cd19886bdf7ee4cfe2e9a0aeaf1525d77ee5f6c3))

## [0.1.2](https://github.com/oddrationale/deepagents-azure-blob-backend/compare/deepagents-azure-blob-backend-v0.1.1...deepagents-azure-blob-backend-v0.1.2) (2026-03-07)


### Bug Fixes

* harden backend file operations ([#15](https://github.com/oddrationale/deepagents-azure-blob-backend/issues/15)) ([c0b6146](https://github.com/oddrationale/deepagents-azure-blob-backend/commit/c0b6146e7541f5c009f4373dece6e2bb8560b237))

## [0.1.1](https://github.com/oddrationale/deepagents-azure-blob-backend/compare/deepagents-azure-blob-backend-v0.1.0...deepagents-azure-blob-backend-v0.1.1) (2026-03-07)


### Features

* Azure Blob Storage backend for Deep Agents ([#1](https://github.com/oddrationale/deepagents-azure-blob-backend/issues/1)) ([b815007](https://github.com/oddrationale/deepagents-azure-blob-backend/commit/b815007f185d229793013429dfcbc2f85cd41ed0))

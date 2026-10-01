# Security Policy

## Supported Versions

This package is deprecated and no longer maintained. No versions receive security fixes.

| Version | Supported |
| ------- | --------- |
| all     | :x:       |

Use [`langchain-azure-storage`](https://pypi.org/project/langchain-azure-storage/) instead — see the [migration guide](https://github.com/oddrationale/deepagents-azure-blob-backend#migrating-to-langchain-azure-storage). Report vulnerabilities in its Azure Blob Storage backend to [langchain-ai/langchain-azure](https://github.com/langchain-ai/langchain-azure).

## Reporting a Vulnerability

If you discover a security vulnerability in this package, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainers or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
3. Include a description of the vulnerability and steps to reproduce

We aim to acknowledge reports within 48 hours and provide a fix within 7 days for critical issues.

## Security Considerations

- This package uses `DefaultAzureCredential` by default, which follows the Azure SDK credential chain. Ensure your environment is configured securely.
- Connection strings should never be committed to version control. Use environment variables or Azure Key Vault.
- The `prefix` configuration option provides namespace isolation but is not a security boundary. Use separate containers or storage accounts for true tenant isolation.

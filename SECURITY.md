# Security and privacy policy

## Supported version

Security maintenance applies to the latest published MiND release.

## Data boundary

MiND stores Cycle Artifacts locally in JSONL or SQLite. Selecting a commercial
provider sends the configured request to that provider under the user's own
account and terms. The offline mock sends no interaction content outside the
computer.

MiND does not automatically redact personal, confidential or regulated data.
Embedding applications remain responsible for data minimization, consent,
redaction and retention policy before a request reaches a commercial provider.

## Credentials

The Windows application stores provider keys for the current user through
Windows Credential Manager. Headless deployments may use process environment
variables. Keys are not part of Cycle Artifacts, exports, backups or settings
responses.

Never commit `.env`, `.env.local`, API keys or credential exports. The repository
ignores local environment files and CI scans tracked text for common key forms.

## Local service

The visual interface binds to the local computer. MiND 1.0.5 is not designed as
an internet-facing multi-user service. Operators who expose the HTTP API beyond
localhost must add authentication, transport encryption, access control and
rate limiting appropriate to their environment.

## Integrity and deletion

The Cycle Artifact is an audit record, not a cryptographic proof. Local users
with filesystem access can modify or delete the database. Export and backup
files should therefore be protected according to their sensitivity.

Deletion from the interface is intentionally explicit and irreversible. Create
a backup before clearing local records when retention is required.

## Reporting a vulnerability

Do not publish credentials or sensitive proof-of-concept data in a public issue.
Use the repository owner's private contact route on GitHub and include the
affected version, impact, reproduction steps and a minimally sensitive example.

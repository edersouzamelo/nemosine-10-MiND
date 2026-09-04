# Response to prior MiND review concerns

This document maps the previously reported concerns to evidence in the current
release candidate. It is a preparation record and can be adapted to the actual
editorial form if the journal requests a point-by-point response.

## 1. Installable public software

**Earlier concern:** The software was not readily installable from a standard
distribution channel.

**Current response:** MiND has a base Python package with optional extras, a
tested wheel and source distribution, a public release workflow for PyPI, and a
self-contained Windows MSI. Clean-wheel and Windows installation tests run in
public GitHub Actions. The final stable tag and PyPI visibility will be confirmed
before submission.

## 2. Implementation depth

**Earlier concern:** The code appeared too basic for the claims.

**Current response:** The implementation now includes a provider protocol,
versioned Cycle Artifact, structured failures, JSON Lines and SQLite stores,
migration, paginated retrieval, public Python API, CLI, versioned HTTP API,
local UI, export, backup, retention controls, and Windows packaging. The paper
also narrows its claim: MiND is a minimal audit middleware, not a semantic
reasoning or agent framework.

## 3. More than one provider

**Earlier concern:** The reference implementation supported only one LLM API.

**Current response:** MiND provides OpenAI and Anthropic adapters plus an offline
deterministic mock. The commercial adapters are optional and tested against
simulated SDK clients. The paper does not claim live-provider availability as an
invariant of the middleware.

## 4. Documentation and evaluation

**Earlier concern:** Documentation and evidence were limited.

**Current response:** The repository now includes installation and provider
guidance, an agnostic integration contract, Cycle Artifact documentation,
validation evidence, security and privacy boundaries, a contribution guide,
changelog, citation metadata, legal notices, and a revised software metapaper.
Public CI exercises supported Python versions, minimum dependencies, packaging,
offline execution, and the Windows lifecycle.

## 5. Claim accuracy

**Risk identified during revision:** The earlier manuscript described intent
classification and specialized routing as implemented.

**Current response:** Those claims were removed. Version 1.0.5 uses one explicit
request path. Semantic classification and processing corridors are identified
only as future work. MiND records observable interaction data and does not claim
to read human or model thought.

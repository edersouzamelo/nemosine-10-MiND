---
title: "MiND: Minimal Deterministic Middleware for Auditable Large Language Model Interactions"
tags:
  - large language models
  - middleware
  - auditability
  - provenance
  - research software
authors:
  - name: Edervaldo José de Souza Melo
    affiliation: 1
affiliations:
  - name: Independent Researcher, Brazil
    index: 1
date: 2026-09-04
bibliography: paper.bib
---

## Abstract

Large language models are increasingly embedded in research software, but a
typical integration sends a prompt directly to a provider and retains little
structured evidence about the request, response, configuration, timing, and
failure conditions. MiND is an open-source, provider-neutral middleware that
places a small audit boundary between an application and a language model. For
each attempted interaction, MiND normalizes the input, constructs an explicit
request, invokes a selected provider adapter, normalizes the result, and stores
a versioned Cycle Artifact. The artifact includes a local identifier, UTC
timestamps, duration, public configuration, provider metadata, output, and safe
error information. The same core is available through a Python API, command-line
interface, local HTTP API, and a Windows desktop installer with a browser-based
local control center. JSON Lines and SQLite storage are supported, as are an
offline deterministic mock and optional OpenAI and Anthropic adapters. MiND is
non-agentic and does not inspect model internals, infer human intention, or
guarantee repetition of stochastic model output. Its contribution is a minimal,
inspectable, reusable execution record for studies and applications that need
procedural traceability around LLM calls.

## Statement of need

Foundation models have become general components of research and software
workflows [@bommasani2021opportunities]. Their practical convenience can conceal
an important methodological gap. In a direct application-to-provider call, the
visible prompt and answer may be retained while execution parameters, request
construction, provider identifiers, timestamps, latency, token usage, failure
categories, and local configuration are scattered across logs or not retained
at all. Provider-managed conversation histories are useful user features, but
they are not a provider-neutral provenance layer controlled by the researcher.

This gap affects auditability before it affects exact reproducibility. A
researcher examining an earlier result first needs to know what was submitted,
which adapter and model were selected, which public parameters were used, what
the provider returned, and whether the record describes a success or failure.
Without a structured unit that connects these elements, post-hoc inspection
depends on informal notes and application-specific logs. The resulting evidence
is hard to query, migrate, compare, or preserve.

The problem is intensified by the probabilistic and externally managed nature
of commercial LLMs. Exact output reproduction may be impossible even when a
nominal model and prompt are unchanged. Models can be updated by providers,
sampling can vary, and remote conditions are outside the caller's control. MiND
therefore uses a deliberately bounded meaning of reproducibility. It records
the defined request procedure and observed result so an execution can be
inspected or attempted again. It does not claim that a third-party model will
return identical text. This distinction follows broader calls for explicit
documentation of model and data conditions [@mitchell2019modelcards;
@gebru2021datasheets] and transparent computational reporting
[@pineau2021improving].

MiND was created for researchers and developers who need a small integration
layer rather than a full agent framework. Its main use cases include recording
LLM-assisted research steps, comparing providers under documented request
conditions, retaining locally queryable evidence for an application, and
adding an audit boundary to existing Python or HTTP software. It is especially
useful where the embedding system should own its records instead of relying on
one provider's conversation history.

Existing observability platforms can offer rich hosted tracing, evaluation, or
team dashboards. MiND addresses a narrower need: a lightweight local reference
implementation with no mandatory runtime dependency, a deterministic offline
mode, two simple storage options, and a versioned provider-neutral artifact. It
can be installed as a Python library or as a self-contained Windows application.
This local-first scope keeps the audit mechanism usable in teaching,
prototyping, independent research, and environments where an additional hosted
service is undesirable.

## Software design

### Execution boundary

MiND mediates one explicit processing path. The embedding application supplies
text and an externally selected configuration. MiND normalizes the text,
constructs a system and user message list, calls the configured provider,
normalizes the provider result, persists an artifact, and returns the response
with a `cycle_id`. If the provider fails, MiND persists a failed artifact with a
safe structured error and then reports the failure to the caller.

The core is intentionally non-agentic. It does not formulate goals, plan
multiple steps, select tools, create sub-agents, or autonomously choose a
provider. The current version also does not classify semantic intent or route
requests through specialized processing corridors. Those ideas may be studied
as future extensions, but describing them as implemented would overstate the
software. If routing is added later, its decision and rule version should be
recorded explicitly in the artifact rather than hidden in model-generated text.

This limited control path gives the term *deterministic middleware* a precise
meaning. Given the same MiND version, public configuration, normalized input,
and provider result, the middleware performs the same ordered operations and
uses the same artifact schema. The offline mock is deterministic and returns a
predictable response for a given input. A commercial provider is an external
component and can remain stochastic. Unique cycle identifiers, timestamps, and
durations also vary by execution, as expected for provenance fields.

### Provider abstraction

Providers implement a small protocol with `name`, `model`, and `generate`.
`generate` receives the explicit message list, temperature, and maximum output
tokens, and returns provider-neutral text plus optional request identifier,
finish reason, and usage data. MiND includes three adapters:

1. `MockProvider`, an offline deterministic implementation used by tests,
   demonstrations, and first-run evaluation;
2. `OpenAIProvider`, an optional adapter for the OpenAI SDK;
3. `AnthropicProvider`, an optional adapter for the Anthropic SDK.

The base Python package does not install either commercial SDK. Users select
only the extra required for their environment, or install both provider extras.
Adapter errors are converted to a provider-neutral `ProviderError` containing a
safe category, code, retryability flag, and public message. Raw vendor
exceptions are not copied into the audit record because they may contain
unstable or sensitive details.

The abstraction is also the Plug and Play integration point. An arbitrary
application does not become compatible merely by supplying its GitHub URL. It
must call MiND at the point where it would otherwise call an LLM, using the
Python API or local HTTP endpoint. A custom model service can be connected by
implementing the same provider protocol. No dependency on Nemosine, MCL, or
another named host application is required.

### Cycle Artifact

The primary research object produced by MiND is the Cycle Artifact. Version
1.0.5 writes schema `mind.cycle/1`. Each artifact is a JSON-compatible object
with the following top-level fields:

| Field | Recorded information |
| --- | --- |
| `schema_version` | Artifact contract identifier |
| `cycle_id` | Local lookup identifier |
| `status` | `succeeded` or `failed` |
| `created_at` | UTC start timestamp |
| `completed_at` | UTC completion timestamp |
| `duration_ms` | Middleware-observed elapsed time |
| `input` | Normalized input data |
| `config` | Public execution configuration |
| `provider` | Provider, model, request ID, finish reason, and available usage |
| `output` | Normalized response data |
| `error` | Safe structured error data or `null` |
| `extensions` | Namespace for future metadata |

Required identity, status, duration, and timestamp conditions are validated by
the data model. The artifact contains the observed output rather than a claim
about the model's internal reasoning. It can support statements such as “this
application sent this normalized input under this public configuration and
received this output.” It cannot prove why a human wrote the prompt or why a
model generated a particular token sequence. MiND records the observable
interaction boundary, not either participant's private thought.

The `extensions` object allows future research metadata without silently
changing the meaning of existing fields. A future classifier, routing rule, or
redaction stage should identify its own schema and version inside this object.
This design favors additive evolution while preserving readers for current
artifacts.

### Reference workflow

Consider a research script that asks several model providers to summarize the
same synthetic observation. Without middleware, the script may save only a
table of answers. With MiND, the script creates one middleware instance per
declared provider configuration, sends each observation through `run`, and
stores the returned `cycle_id` in its experimental table. The full artifact can
then be retrieved by identifier when a result is reviewed. This separates the
study's domain data from the execution evidence while preserving a stable link
between them.

During development, the same script can use `MockProvider`. For the input
“summarize observation 17,” the mock returns a predictable prefixed response and
MiND persists the same provider name, model name, public configuration shape,
and output normalization path used by the real adapters. The mock does not
simulate language quality. Its purpose is to test integration, persistence, and
retrieval without a credential, network dependency, or usage cost.

When the researcher enables a commercial adapter, the Cycle Artifact records
the requested model name and any response metadata exposed by the SDK. If the
provider supplies a request identifier, finish reason, or usage counts, those
values are retained under `provider`. If an account lacks access or a remote
request fails, the failed artifact preserves the attempted input, public
configuration, provider and model, elapsed time, and safe error category. This
makes unsuccessful attempts part of the research trail instead of invisible
exceptions.

The researcher can export selected records for a day or date interval from the
local interface, or query the store through Python or HTTP. Current filters are
based on retained artifact fields; MiND does not fabricate semantic topics that
were never recorded. A study needing subject labels or heuristics can add them
in its own data model or in a versioned artifact extension. This example
illustrates the intended division of responsibility: MiND preserves the
observable LLM interaction boundary, while study-specific interpretation stays
with the research workflow.

### Persistence

MiND provides JSON Lines and SQLite stores behind a common interface. JSON Lines
offers transparent append-only records that can be inspected with standard text
tools. The writer flushes and synchronizes each completed line. The reader can
ignore an incomplete final line left by an interrupted write, while malformed
complete records are reported as corruption rather than silently discarded.

SQLite provides indexed lookup by `cycle_id`, reverse chronological listing,
pagination, and local transactional persistence. Write-ahead logging and a busy
timeout support ordinary local concurrency. Both stores expose append, lookup,
list, and latest-record operations. A migration function copies readable legacy
JSON Lines data into the current store while preserving its declared schema
identity.

Storage is local by default. The visual interface can report occupied space,
export filtered records as JSON, create a full local backup, and clear retained
records after explicit confirmation. Version 1.0.5 does not include Google
Drive synchronization, automatic cloud backup, or a Supabase dependency. These
are deployment choices rather than requirements of the audit core.

### Interfaces and distribution

The same runtime can be reached through four surfaces. The public Python API
offers `Mind.create()`, `run()`, `get_cycle()`, and `list_cycles()`. The `mind`
command-line interface provides offline demonstration, execution, diagnostics,
history, migration, HTTP service, and local UI commands. A versioned HTTP API
under `/v1` accepts interactions and returns stored artifacts. A static local
web interface is served by the HTTP component.

For Windows users, a self-contained MSI packages the Python runtime,
dependencies, providers, local controller, and interface. Installation creates
Start Menu and desktop shortcuts. The controller starts MiND on the local
computer, opens the interface, and allows the service to be stopped. The MSI is
tested on a clean hosted Windows runner for installation, launch, HTTP response,
upgrade behavior, and uninstall. The current preview is not code-signed, so the
operating system or antivirus software can warn that the publisher is unknown.

The Windows interface can configure mock, OpenAI, or Anthropic use. Provider
keys entered through the Windows application are stored for the current user in
Windows Credential Manager. Headless deployments can use process environment
variables. Keys are not returned by the settings API and are not intentionally
written to Cycle Artifacts, exports, backups, or repository files.

## Quality control

MiND uses automated tests and public continuous integration as the principal
validation mechanism. At the 1.0.5 release candidate, the suite contains tests
for core orchestration, provider contracts, safe failures, Cycle Artifact
validation, JSON Lines recovery, SQLite behavior, migration, Python API, CLI,
HTTP endpoints, UI assets, settings, credential handling, legal files, and
packaging. Coverage is required to remain at or above 85 percent branch-aware
measurement.

The CI matrix runs on Python 3.9, 3.10, 3.11, 3.12, and 3.13. A separate job
installs declared minimum dependencies. Quality jobs run Ruff formatting and
lint checks plus MyPy static type checks. Packaging jobs build wheel and source
distributions, run `twine check`, inspect required UI and legal files inside the
wheel, install the base wheel without dependencies in a fresh virtual
environment, and execute the offline demonstration. The fresh environment also
verifies that FastAPI, OpenAI, and Anthropic are not pulled into the base
installation.

The Windows workflow builds the executable bundle and MSI, generates third-party
license notices from the resolved environment, installs the package silently on
a clean runner, checks shortcuts and installed files, starts the service,
requests the health and interface endpoints, tests upgrade installation, and
uninstalls the product. Published MSI assets include a SHA-256 digest.

Commercial provider adapters are tested with simulated SDK clients. This proves
request construction, result normalization, and failure mapping without paid
network calls or secrets in CI. It does not prove continuing availability,
billing state, account permissions, or behavior of a remote provider. Live
provider validation remains an environment-specific integration test and is not
required for the bounded claims made here.

The validation record, including public workflow URLs and explicit limitations,
is maintained in `docs/VALIDATION.md`. Security assumptions and reporting
guidance are documented in `SECURITY.md`. Documentation tests prevent known
unimplemented features from being reintroduced into the paper as current
claims.

## Reuse potential

MiND can be reused as an audit boundary in a Python application with a small
number of calls. An existing service can instead post to the local HTTP API and
retain the returned `cycle_id` alongside its own domain record. A laboratory can
use the deterministic mock to validate its integration without network access,
then enable a commercial or custom provider for authorized experiments. The
provider protocol permits local models and additional vendors without changing
the orchestrator or storage contract.

Cycle Artifacts can be joined with experiment identifiers through the extension
field or through the embedding application's database. Their JSON-compatible
shape makes export to notebooks, data frames, archival packages, or institutional
repositories straightforward. JSON Lines supports transparent review, while
SQLite supports local queries and pagination. Because the record format is
provider-neutral, a study can retain comparable boundary metadata while
switching adapters.

The software is deliberately small enough to serve as a teaching reference for
provenance-aware LLM integration. It demonstrates separation of credentials,
public configuration, provider response metadata, storage, and user interfaces.
Contributors can add an adapter without placing vendor code in the core.

Potential reuse must respect the security boundary. MiND is not a privacy
filter, content moderation system, cryptographic ledger, or internet-facing
multi-user service. An embedding application handling sensitive information
must apply its own consent, minimization, redaction, access control, and retention
policy before a commercial provider call. Local users with filesystem access
can alter local records, so an artifact is evidence for inspection rather than
tamper-proof proof.

Future work may evaluate cryptographic integrity, standardized provenance
exports based on W3C PROV [@lebo2013prov], configurable redaction stages, and
deterministic routing through versioned processing corridors. Such work should
preserve the principle that every transformation and routing decision is
observable. These features are not included in the present release.

## Availability

- **Operating system:** Core package is operating-system independent; the
  self-contained graphical installer targets 64-bit Windows.
- **Programming language:** Python 3.9 or later.
- **Additional system requirements:** None for the base package and offline
  mock. The local HTTP interface uses optional Python dependencies. Commercial
  providers require network access, their optional SDK, a provider account, and
  a user-supplied credential.
- **Dependencies:** The base package has no mandatory runtime dependencies.
  Optional dependency groups are declared in `pyproject.toml`.
- **Source code repository:**
  <https://github.com/edersouzamelo/nemosine-10-MiND>
- **Version reviewed in this paper:** 1.0.5 release candidate, commit
  `968eee6ef68efbe47529c01ed383dbfa94a36369` plus the S8 and S9 documentation
  revision.
- **Windows preview archive:**
  <https://github.com/edersouzamelo/nemosine-10-MiND/releases/tag/v1.0.5-windows-preview.1>
- **Long-term archive:** A version-specific Zenodo DOI for the final 1.0.5
  release must replace this sentence before submission. The earlier project
  archive is <https://doi.org/10.5281/zenodo.18637799> and does not by itself
  certify the present revision.
- **License:** Apache License 2.0. The MiND name and logo are governed separately
  by `TRADEMARKS.md`.

## Research software metadata

The repository contains `CITATION.cff`, an Apache 2.0 license, copyright and
attribution notice, trademark policy, third-party notices, security policy,
contribution guide, changelog, architecture contract, and validation record.
Releases provide source archives automatically through GitHub. A final stable
tag and version-specific preservation record are release prerequisites for JORS
submission [@smith2016softwarecitation; @wilkinson2016fair].

## Limitations

MiND observes only the application-provider boundary. It cannot inspect hidden
provider prompts, proprietary infrastructure, model weights, latent states, or
human cognition. The recorded prompt is an input, not a verified statement of
human intent. The output is an observation, not a direct representation of a
model's reasoning. Metadata availability varies by provider.

The current request builder creates one system message and one normalized user
message. Multi-turn context policy, tool calls, multimodal inputs, streaming
token events, semantic classification, and specialized routing corridors are
outside the present runtime. The storage layer is designed for local use rather
than high-volume distributed ingestion. The local interface is not a hosted
progressive web application and has no multi-user authentication.

These constraints are intentional boundaries of a minimal reference
implementation. They also define concrete evaluation targets for future work.

## Acknowledgements

The author acknowledges the maintainers of the open-source Python, FastAPI,
SQLite, packaging, and testing ecosystems used to build and validate the
software. No generative model is listed as an author.

## Author contributions

Edervaldo José de Souza Melo: conceptualization, software, methodology,
validation, investigation, documentation, visualization, and writing.

## Competing interests

The author declares no competing interests.

## References

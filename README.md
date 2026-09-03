# MiND

**MiND: A Minimal Deterministic Middleware for Auditable LLM Interaction**

MiND is a lightweight, provider-neutral middleware designed to mediate
interactions between applications and large language models (LLMs). It provides
a deterministic execution and audit layer that normalizes inputs, assembles
requests, records provider responses, and persists versioned Cycle Artifacts
without modifying the underlying models.

The name **MiND** originally refers to *Minimal Nemosine Design*. In the context of this repository and its associated software publication, MiND is used to denote a **Minimal Deterministic Middleware** for auditable LLM interaction. This naming reflects the architectural role of the system while remaining consistent with its origin as an extracted core from the broader Nemosine framework.

Legacy AME imports remain available only as a temporary compatibility layer. The
active implementation lives in the neutral `nemosine_mind.core` package.


---

## Overview

Large Language Models (LLMs) are increasingly integrated into workflows involving sensitive data, iterative reasoning, and long-term user interaction. Despite this growing adoption, most LLM-based applications still rely on direct submission of unstructured prompts to proprietary model APIs. This interaction paradigm offers limited control over:

- Data exposure and privacy
- Traceability and auditability
- Portability of user interaction histories
- Post-hoc inspection of model behavior

MiND addresses these limitations by introducing a deterministic middleware layer
positioned between applications and LLMs. In the current implementation, MiND
normalizes the input, builds an explicit request, calls the selected provider,
normalizes the result, and records the interaction before returning it to the
client.

MiND is explicitly non-agentic. It does not perform autonomous planning, goal formulation, multi-step reasoning, tool orchestration, or adaptive control. The middleware operates strictly as a deterministic and externally controlled interaction layer.

MiND does not implement fine-tuning, RLHF, model alignment techniques, or internal model modification. Any agent-like behavior, if desired, must be implemented externally and remains out of scope for this software.

---

## Installation and Minimal Test

The current Windows preview is available from the repository's
[Releases](https://github.com/edersouzamelo/nemosine-10-MiND/releases) page. It
contains a self-contained installer and local visual interface.

For Python development from the recovery branch:

```bash
python -m pip install "nemosine-mind[ui] @ git+https://github.com/edersouzamelo/nemosine-10-MiND.git@agent/mind-s1-core-recovery"
mind demo "hello"
mind ui
```

The offline mock requires no API key. It returns a predictable test response and
a `cycle_id`. OpenAI and Anthropic require their optional SDKs and a provider
credential.

### Provider credentials

The Windows application configures providers from the **Seletor de LLM** panel.
OpenAI and Anthropic keys are stored in Windows Credential Manager for the current
user. They are never written to Cycle Artifacts, reports, application settings, or
the Git repository.

For development and headless usage, MiND also accepts `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY` from the process environment. Copy `.env.example` to a local
`.env.local` only if your launcher loads that file. All `.env.*` files are ignored
by Git except sanitized examples.

---

## Design Principles

MiND is built around the following core principles:

- **Determinism**  
  The middleware itself is non-agentic and deterministic. It does not perform autonomous planning or decision-making.

- **Externalized State**  
  Requests, provider results, and audit records are handled explicitly outside
  the LLM. Future routing decisions and semantic extensions will also be recorded
  outside the model when implemented.

- **Auditability**  
  Every interaction generates structured artifacts, enabling inspection and post-hoc analysis without access to model internals.

- **API Agnosticism**  
  MiND is designed to operate independently of any specific LLM provider or API.

- **Minimalism**  
  The framework provides a minimal executable core intended as architectural infrastructure, not as a full application or agent framework.

---

## Architecture

MiND currently executes one explicit processing path: normalize input, assemble the
request, call the selected provider, normalize its result, and persist a versioned
Cycle Artifact. Provider selection is explicit and does not give the software
autonomous goals, planning, memory, or tool choice.

Intent classification, deterministic routing through specialized processing
corridors, context retrieval, semantic heuristics, and policy modules are planned
extensions. They are not part of the current runtime and are not claimed as
implemented capabilities.

During execution, MiND generates structured artifacts, including:

- JSON-based interaction logs
- Persistent records stored in a relational database (optional)

As a result, request construction, provider execution, response delivery, and the
associated metadata become inspectable records rather than opaque side effects of
a provider-managed conversation history.

---

## Practical Capabilities

By externalizing interaction state and control logic, MiND enables several practical capabilities:

- **Auditable interaction trails**  
  Creation of structured logs for LLM usage without requiring access to model internals.

- **Portability across LLM providers**  
  Preservation of user interaction histories when switching between different LLM APIs.

- **External behavioral constraints**  
  Experimentation with response formats, policies, or interaction rules without fine-tuning or modifying the underlying models.

---

## Scope and Non-Goals

MiND is designed as middleware infrastructure and deliberately avoids several common claims:

- It does **not** attempt to infer causal mechanisms inside LLMs.
- It does **not** replace model fine-tuning, RLHF, or training-based alignment methods.
- It is **not** an autonomous agent framework.

Its contribution lies in providing a controlled, inspectable, and reproducible interaction layer around existing LLMs.

---

## Example Use Case

In a research workflow comparing LLM providers, MiND can be configured to:

- Log all interactions in structured form
- Store interaction traces locally
- Avoid reliance on provider-specific conversation histories

This enables traceable experimentation and post-hoc auditing across providers.
Applications handling sensitive data still need their own redaction and governance
controls before sending content to a commercial provider.

---

## Target Audience

MiND is intended for:

- Researchers requiring reproducible LLM experiments with controlled prompt construction
- Developers building privacy-sensitive LLM applications
- Organizations needing auditable AI interaction logs for compliance or post-hoc analysis

---

## Relationship to Nemosine

MiND originates as the minimal executable core extracted from the broader **Nemosine** cognitive architecture. While Nemosine encompasses higher-level symbolic, modular, and theoretical constructs, MiND focuses exclusively on the minimal deterministic middleware required to operationalize controlled LLM interaction.

MiND can be used independently and does not require adoption of the broader Nemosine framework.

---

## License

MiND is licensed under the **Apache License, Version 2.0**.

Copyright 2026 Edervaldo José de Souza Melo.

The Apache License permits use, modification, reproduction, and distribution,
including commercial use, subject to its terms.

See:

- `LICENSE`: full Apache License 2.0 text
- `NOTICE`: copyright and attribution notice
- `TRADEMARKS.md`: policy for the MiND name, logo, and project branding
- `THIRD_PARTY_NOTICES.txt`: third-party licensing and release-audit policy

The MiND name, logo, visual identity, and other project identifiers are not
licensed as branding under the Apache License 2.0.

---

## Author

**Edervaldo José de Souza Melo**  
Independent Researcher — Brazil  

---

## Status

- Executable minimal architecture
- Deterministic and non-agentic
- Auditable via structured logs
- Designed as architectural infrastructure, not a final product

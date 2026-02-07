# MiND

**MiND: A Minimal Deterministic Middleware for Auditable LLM Interaction**

MiND is a lightweight, API-agnostic middleware designed to mediate interactions between users and large language models (LLMs). It provides a deterministic orchestration layer that enables structured preprocessing, routing, and logging of prompts and responses without modifying the underlying models.

The name **MiND** originally refers to *Minimal Nemosine Design*. In the context of this repository and its associated software publication, MiND is used to denote a **Minimal Deterministic Middleware** for auditable LLM interaction. This naming reflects the architectural role of the system while remaining consistent with its origin as an extracted core from the broader Nemosine framework.

Internally, the reference implementation still is called AME ("arquiteura Mínima Executável). In this repository, AME corresponds directly to MiND and represents its executable reference implementation.


---

## Overview

Large Language Models (LLMs) are increasingly integrated into workflows involving sensitive data, iterative reasoning, and long-term user interaction. Despite this growing adoption, most LLM-based applications still rely on direct submission of unstructured prompts to proprietary model APIs. This interaction paradigm offers limited control over:

- Data exposure and privacy
- Traceability and auditability
- Portability of user interaction histories
- Post-hoc inspection of model behavior

MiND addresses these limitations by introducing a deterministic middleware layer positioned between users and LLMs. Instead of forwarding raw user inputs directly to a model, MiND performs structured preprocessing, routing, and logging of interactions before and after each model invocation.

MiND is explicitly non-agentic. It does not perform autonomous planning, goal formulation, multi-step reasoning, tool orchestration, or adaptive control. The middleware operates strictly as a deterministic and externally controlled interaction layer.

MiND does not implement fine-tuning, RLHF, model alignment techniques, or internal model modification. Any agent-like behavior, if desired, must be implemented externally and remains out of scope for this software.

---

## Design Principles

MiND is built around the following core principles:

- **Determinism**  
  The middleware itself is non-agentic and deterministic. It does not perform autonomous planning or decision-making.

- **Externalized State**  
  Interaction state, context updates, and routing decisions are handled explicitly outside the LLM, rather than being embedded implicitly in conversational history.

- **Auditability**  
  Every interaction generates structured artifacts, enabling inspection and post-hoc analysis without access to model internals.

- **API Agnosticism**  
  MiND is designed to operate independently of any specific LLM provider or API.

- **Minimalism**  
  The framework provides a minimal executable core intended as architectural infrastructure, not as a full application or agent framework.

---

## Architecture

MiND operates by classifying incoming inputs into predefined processing modules. Each module is responsible for a restricted subset of the interaction context, such as:

- Input classification
- Context retrieval
- Prompt assembly
- Response handling and validation

By isolating these responsibilities, MiND prevents unintended cross-contamination of conversational state and makes each processing step explicit and inspectable.

During execution, MiND generates structured artifacts, including:

- JSON-based interaction logs
- Persistent records stored in a relational database (optional)

As a result, prompt construction, context updates, and response delivery become explicit steps rather than opaque side effects of conversational history managed by external platforms.

---

## Practical Capabilities

By externalizing interaction state and control logic, MiND enables several practical capabilities:

- **Auditable interaction trails**  
  Creation of structured logs for LLM usage without requiring access to model internals.

- **Reduced data exposure**  
  Limiting the information transmitted to each individual model invocation, including optional redaction or symbolic encoding of sensitive data.

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

In a research workflow involving sensitive medical data, MiND can be configured to:

- Log all interactions in structured form
- Redact patient identifiers before model invocation
- Store interaction traces locally
- Avoid reliance on provider-specific conversation histories

This enables reproducible experimentation and auditing while minimizing data exposure.

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

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

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

---
title: "MiND: A Minimal Deterministic Middleware for Auditable LLM Interaction"
tags:
  - large language models
  - middleware
  - auditability
  - reproducibility
authors:
  - name: Edervaldo José de Souza Melo
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 2026-02-07
bibliography: paper.bib
---

## Summary

MiND is a lightweight, API-agnostic middleware designed to mediate interactions between users and large language models (LLMs). It provides a deterministic orchestration layer that enables structured preprocessing, routing, and logging of prompts and responses without modifying the underlying models. MiND is explicitly non-agentic: it does not perform autonomous planning, goal formulation, tool invocation, or adaptive control. By externalizing interaction state and control logic, MiND supports auditable usage, reduced data exposure, and portability of user interaction histories across different LLM providers. The middleware is intended for developers and researchers who require controlled, inspectable, and reproducible LLM interaction pipelines beyond direct prompt-to-API usage.

## Statement of Need

Large Language Models (LLMs), typically based on Transformer architectures [@vaswani2017attention], are increasingly integrated into workflows involving sensitive data, iterative reasoning, and long-term interaction with users. Despite this growing adoption, most LLM-based applications still rely on direct submission of unstructured prompts to proprietary model APIs. This interaction paradigm provides limited control over data exposure, traceability, portability, and post-hoc inspection of model behavior.

The proposed software is explicitly non-agentic. It does not perform autonomous planning, goal formulation, multi-step reasoning, tool orchestration, or adaptive control. MiND operates strictly as a deterministic middleware layer that mediates each interaction with a language model in an explicit, reproducible, and externally controlled manner.

MiND does not implement fine-tuning, RLHF, or model alignment techniques. Any agent-like behavior, if desired, must be implemented outside MiND and remains out of scope for this software.

**MiND** addresses this gap by providing a deterministic orchestration layer positioned between users and LLMs. MiND (Minimal Design) is the minimal, standalone deterministic middleware layer extracted from the broader Nemosine project. In this context, the reference to Nemosine indicates the architectural origin of MiND, while the present software is intentionally scoped as an independent, self-contained middleware component. No knowledge of the broader Nemosine system is required to use or evaluate MiND. Rather than forwarding raw user inputs directly to a language model, MiND performs structured preprocessing, routing, and logging of interactions before and after each model invocation. This approach enables controlled mediation of prompts, explicit state management, and decoupling of user interaction data from any specific LLM provider.

The middleware operates by classifying incoming inputs into predefined processing modules, each responsible for a restricted subset of the interaction context. These modules encapsulate distinct functional roles—such as input classification, context retrieval, and response handling—preventing unintended cross-contamination of conversational state. During execution, MiND generates structured artifacts, including JSON-based interaction logs and persistent records stored in a relational database. As a result, prompt construction, context updates, and response delivery become explicit and inspectable steps rather than opaque side effects of conversational history managed by external platforms.

By externalizing interaction state and control logic, MiND enables several practical capabilities. First, it supports the creation of auditable interaction trails for LLM usage without requiring access to model internals. Second, it reduces unnecessary data exposure by limiting the information transmitted to each individual model invocation (including optional redaction or symbolic encoding of sensitive data). Third, it allows portability of user interaction histories across different LLM APIs, enabling provider substitution without loss of accumulated context. Finally, it facilitates experimentation with externally defined behavioral constraints—such as response validation or interaction policies—without modifying or fine-tuning the underlying models.

For example, in privacy-sensitive workflows, MiND can be configured to selectively redact or symbolically transform user inputs before model invocation, while preserving auditable interaction logs locally. This allows developers to control data exposure and maintain inspection capabilities without relying on provider-specific conversation histories.

MiND is designed as API-agnostic middleware and does not claim to infer causal mechanisms within LLMs. Its contribution lies in providing developers and researchers with a lightweight, reusable infrastructure for controlled, inspectable, and portable LLM interaction pipelines, addressing practical limitations of current prompt-centric usage patterns.

The references below provide minimal contextual grounding for the architectural assumptions underlying MiND, without implying dependency on specific learning, fine-tuning, or agent-based paradigms.

## Software Availability

- **Name:** MiND (Minimal Deterministic Middleware for Auditable LLM Interaction)
- **Repository:** https://github.com/edersouzamelo/nemosine-10-MiND
- **License:** GNU General Public License v3.0 (GPL-3.0)
- **Version:** main branch (snapshot at submission time)

## References  

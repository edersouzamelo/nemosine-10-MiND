---  
title: "MiND: A Minimal Deterministic Middleware for Auditable LLM Interaction"  
tags:  
  - large language models  
  - middleware  
  - reproducibility  
  - auditability  
authors:  
  - name: Edervaldo José de Souza Melo  
    affiliation: 1  
affiliations:  
  - name: Independent Researcher, Brazil  
    index: 1  
date: 2026-02-xx  
bibliography: paper.bib  
---

## Summary

MiND is a lightweight, API-agnostic middleware designed to mediate interactions between users and large language models (LLMs). It provides a deterministic orchestration layer that enables structured preprocessing, routing, and logging of prompts and responses without modifying the underlying models. MiND is explicitly non-agentic: it does not perform autonomous planning, goal formulation, tool invocation, or adaptive control. By externalizing interaction state and control logic, MiND supports auditable usage, reduced data exposure, and portability of user interaction histories across different LLM providers. The middleware is intended for developers and researchers who require controlled, inspectable, and reproducible LLM interaction pipelines beyond direct prompt-to-API usage.

## Statement of Need

Large Language Models (LLMs), typically based on Transformer architectures [@vaswani2017attention], are increasingly integrated into workflows involving sensitive data, iterative reasoning, and long-term interaction with users. Despite this growing adoption, most LLM-based applications still rely on direct submission of unstructured prompts to proprietary model APIs. This interaction paradigm provides limited control over data exposure, traceability, portability, and post-hoc inspection of model behavior.

The proposed software is not an autonomous agent middleware. It does not perform goal formulation, multi-step planning, self-directed action, tool orchestration, or feedback-driven adaptation. MiND operates strictly as a deterministic middleware layer that mediates each interaction with a language model in an explicit, reproducible, and externally controlled manner. Any higher-level agent behavior, if desired, must be implemented outside MiND and remains out of scope for this software.

**MiND** addresses this gap by providing a deterministic orchestration layer positioned between users and LLMs. MiND is the minimal, standalone orchestration layer extracted from the broader Nemosine framework. Rather than forwarding raw user inputs directly to a language model, MiND performs structured preprocessing, routing, and logging of interactions before and after each model invocation. This approach enables controlled mediation of prompts, explicit state management, and decoupling of user interaction data from any specific LLM provider.

The middleware operates by classifying incoming inputs into predefined processing modules, each responsible for a restricted subset of the interaction context. These modules encapsulate distinct functional roles—such as input classification, context retrieval, and response handling—preventing unintended cross-contamination of conversational state. During execution, MiND generates structured artifacts, including JSON-based interaction logs and persistent records stored in a relational database. As a result, prompt construction, context updates, and response delivery become explicit and inspectable steps rather than opaque side effects of conversational history managed by external platforms.

By externalizing interaction state and control logic, MiND enables several practical capabilities. First, it supports the creation of auditable interaction trails for LLM usage without requiring access to model internals. Second, it reduces unnecessary data exposure by limiting the information transmitted to each individual model invocation (including optional redaction or symbolic encoding of sensitive data). Third, it allows portability of user interaction histories across different LLM APIs, enabling provider substitution without loss of accumulated context. Finally, it facilitates experimentation with externally defined behavioral constraints—such as response validation or interaction policies—without modifying or fine-tuning the underlying models.

For example, in privacy-sensitive workflows, MiND can be configured to log interactions in structured form, redact identifiers before model invocation, and store interaction traces locally without relying on provider-specific conversation histories.

MiND is designed as API-agnostic middleware and does not claim to infer causal mechanisms within LLMs. Its contribution lies in providing developers and researchers with a lightweight, reusable infrastructure for controlled, inspectable, and portable LLM interaction pipelines, addressing practical limitations of current prompt-centric usage patterns.

The references below provide minimal contextual grounding for the architectural assumptions underlying MiND, without implying dependency on specific learning, fine-tuning, or agent-based paradigms.

## References  

# Draft cover letter for JORS

Dear Editors,

Please consider the software metapaper “MiND: Minimal Deterministic Middleware
for Auditable Large Language Model Interactions” for publication in the Journal
of Open Research Software.

MiND is an Apache-2.0-licensed, provider-neutral middleware that places a local
audit boundary between an embedding application and a large language model. It
creates a versioned Cycle Artifact for each successful or failed interaction,
recording the normalized input, public execution configuration, provider
metadata, output, timing, and safe error information. The software can be used
through Python, a command-line interface, a local HTTP API, or a self-contained
Windows interface. It supports JSON Lines and SQLite persistence, an offline
deterministic mock, and optional OpenAI and Anthropic adapters.

The revised submission deliberately limits its scientific claims to implemented
and publicly validated behavior. MiND does not claim exact reproduction of
stochastic model outputs, access to model internals, inference of human intent,
or implemented semantic routing. Public continuous integration validates the
supported Python matrix, minimum dependencies, quality checks, clean package
installation, offline execution, and the Windows install, launch, upgrade, and
uninstall lifecycle.

The source, tests, documentation, release artifacts, and version-specific
archive are publicly available at the locations listed in the manuscript.

I confirm that this work is original, is not under consideration elsewhere, and
that I approve its submission. I declare no competing interests.

Sincerely,

Edervaldo José de Souza Melo  
Independent Researcher, Brazil  
[AUTHOR EMAIL TO CONFIRM]  
[ORCID, IF APPLICABLE]

# MiND 1.0.5 validation record

This document defines the evidence supporting the public claims of MiND 1.0.5.
It is a validation record, not a claim that every external provider condition has
been reproduced.

## Validated scope

MiND is a local, provider-neutral middleware that performs one controlled path:

1. normalize a text input;
2. assemble an explicit request;
3. call the selected provider adapter;
4. normalize the provider result;
5. persist a versioned `mind.cycle/1` Cycle Artifact;
6. return the response and `cycle_id`.

The middleware is deterministic with respect to its own control procedure and
the offline mock. Commercial LLM output is not claimed to be deterministic.

## Evidence matrix

| Claim | Evidence | Result |
| --- | --- | --- |
| Core works on supported Python versions | CI matrix on Python 3.9, 3.10, 3.11, 3.12 and 3.13 | Pass |
| Base package has no mandatory provider or HTTP SDK | Clean-wheel smoke test with `--no-deps` | Pass |
| Mock demonstration works without a key or network | `mind demo`, `mind doctor` and cycle query in isolated virtual environment | Pass |
| Cycle Artifacts validate required identity, status, UTC timestamps and duration | Automated model and storage tests | Pass |
| JSONL and SQLite stores support append, lookup and paginated history | Automated storage tests | Pass |
| Legacy JSONL can be read and migrated to SQLite | Automated migration test | Pass |
| OpenAI and Anthropic adapters satisfy the provider contract | Unit tests with simulated SDK clients | Pass |
| Provider failures produce safe audit metadata | Automated provider and HTTP tests | Pass |
| API keys are not returned by the settings API or written to cycle records | Settings, UI and secret-protection tests | Pass |
| Windows installer contains the UI, providers and legal notices | Windows packaging workflow and MSI smoke installation | Pass |
| Windows install, upgrade and uninstall complete | Windows workflow in clean hosted runners | Pass |
| Source and distributions are internally consistent at version 1.0.5 | Version and package tests plus `twine check` | Pass |

## Reproducible commands

```bash
python -m pip install --upgrade pip
python -m pip install ".[dev]"
ruff check src tests packaging
ruff format --check src tests packaging
mypy
python -m pytest --cov=nemosine_mind --cov-report=term-missing
python -m build
twine check dist/*
```

The public CI workflow repeats these checks and additionally installs the built
wheel in a fresh virtual environment.

## Release evidence

- Stable source revision: `c96c43473e4fa51d8b3576825cd60aa8fa4430ed`
- Stable `main` CI run: <https://github.com/edersouzamelo/nemosine-10-MiND/actions/runs/33830901723>
- PyPI publication run: <https://github.com/edersouzamelo/nemosine-10-MiND/actions/runs/33832222783>
- Windows run: <https://github.com/edersouzamelo/nemosine-10-MiND/actions/runs/33804353029>
- Windows preview release: <https://github.com/edersouzamelo/nemosine-10-MiND/releases/tag/v1.0.5-windows-preview.1>
- Stable release: <https://github.com/edersouzamelo/nemosine-10-MiND/releases/tag/v1.0.5>
- PyPI: <https://pypi.org/project/nemosine-mind/1.0.5/>
- Version-specific archive: <https://doi.org/10.5281/zenodo.22291450>
- MSI SHA-256: `8fd06c1999bc4e955bc75221c3ae589b579805d8d110fa505c8fa22ed17c7700`

## Explicit limits

- No live paid call is part of the public test suite. OpenAI and Anthropic are
  contract-tested with simulated clients. Provider availability, billing,
  account permissions and remote model behavior remain external conditions.
- MiND does not inspect model internals, infer causal reasoning or determine the
  true intention of a human or model.
- MiND does not yet classify intent or route requests through specialized
  semantic processing corridors.
- A Cycle Artifact supports procedural traceability. It does not make a
  stochastic provider response exactly reproducible.
- The Windows preview is not code-signed, so Windows or antivirus products can
  display an unknown-publisher warning.
- Google Drive backup, cloud synchronization and a hosted PWA are not part of
  version 1.0.5.

These limits define the boundary of the software metapaper claims.

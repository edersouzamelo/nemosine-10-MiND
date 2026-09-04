# Contributing to MiND

MiND accepts focused contributions that preserve its provider-neutral audit
contract and do not overstate what the software can infer.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[dev]"
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Required checks

```bash
ruff check src tests packaging
ruff format --check src tests packaging
mypy
python -m pytest --cov=nemosine_mind --cov-report=term-missing
python -m build
twine check dist/*
```

New behavior requires tests. Provider integrations should be tested with
simulated clients and must not require paid calls in CI.

## Security and privacy

Do not commit API keys, private prompts or real Cycle Artifact data. Use the
offline mock and synthetic fixtures. Provider errors must be converted to safe,
structured messages before persistence or HTTP delivery.

## Documentation claims

Documentation must distinguish implemented behavior, validated behavior and
planned work. In particular, do not describe intent classification, semantic
routing or exact reproduction of stochastic model output as current features.

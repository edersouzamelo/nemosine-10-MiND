# MiND architecture and integration contract

## Current architecture

MiND is a local middleware, not a hosted service. An embedding application may
use the Python API or HTTP API. Both enter the same runtime and create the same
Cycle Artifact shape.

```text
Embedding application
        |
Python API or HTTP API
        |
MiND orchestrator
        |
Provider adapter
        |
LLM provider or offline mock
        |
Cycle Artifact store (JSONL or SQLite)
```

The current orchestrator has one explicit path. Provider selection is supplied
by configuration. MiND does not autonomously choose a task, tool or model.

## Plug and Play through Python

An application can create and reuse a MiND instance:

```python
from nemosine_mind import Mind

mind = Mind.create()
result = mind.run("Summarize the experiment log")
print(result.reply)
print(result.cycle_id)
```

The embedding system does not need to be Nemosine, MCL or any named project.
Any Python application can use this contract.

## Plug and Play through HTTP

Start the local service:

```bash
python -m pip install "nemosine-mind[http]"
mind serve
```

Send a request:

```http
POST /v1/interactions
Content-Type: application/json

{"text": "Summarize the experiment log"}
```

The response contains the model reply and `cycle_id`. The embedding application
can query `/v1/cycles/{cycle_id}` to retrieve the audit artifact.

A GitHub repository URL alone is not enough to integrate arbitrary software.
The external application must deliberately call the Python or HTTP contract at
the point where it would otherwise call an LLM directly.

## Custom provider adapter

A provider implements the small `Provider` protocol:

```python
from nemosine_mind.providers.base import ProviderResult

class LocalProvider:
    name = "local"
    model = "example-model"

    def generate(self, *, messages, temperature, max_output_tokens):
        text = call_local_model(messages, temperature, max_output_tokens)
        return ProviderResult(text=text)
```

Inject the adapter into the runtime rather than placing credentials or vendor
logic in the core. Adapters should return only safe metadata and should map
vendor exceptions to `ProviderError`.

## Cycle Artifact v1

Each completed or failed provider attempt is recorded as `mind.cycle/1`. Its
top-level fields are:

| Field | Meaning |
| --- | --- |
| `cycle_id` | Local identifier for retrieval |
| `status` | `succeeded` or `failed` |
| `created_at`, `completed_at` | UTC timestamps |
| `duration_ms` | Middleware-observed elapsed time |
| `input` | Normalized input passed to the request builder |
| `config` | Public execution configuration |
| `provider` | Provider, model and available response metadata |
| `output` | Normalized provider output |
| `error` | Safe structured failure data, or `null` |
| `extensions` | Namespaced future metadata |

Credentials must never appear in an artifact.

## Planned semantic routing

Intent classification, semantic heuristics and specialized processing corridors
are a possible future architecture. If implemented, a routing decision must be
external to the LLM, explicitly versioned and written to `extensions` so it can
be inspected. These features are not present in 1.0.5 and are not required to
use MiND as an auditable interaction layer.

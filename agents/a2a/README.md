# agents/a2a/

Agent2Agent (A2A) protocol layer. Built in **Sprint 17** (ROADMAP.md) to close the gap identified
in [IMPROVEMENTS_AND_RESEARCH.md §5](../../IMPROVEMENTS_AND_RESEARCH.md#5-integração-dos-requisitos-de-tributariotxt--complemento-de-add2txt-agosto2026):
the four agents in `agents/` never spoke to each other (or to an external caller) through a
standardized inter-agent protocol — only direct Python calls / LangGraph internals.

```
agents/a2a/
├── agent_card.py   # AgentCard + AgentSkill dataclasses, one card per existing agent
├── server.py       # FastAPI app: GET .well-known/agent.json + POST tasks/send, per agent_id
└── client.py        # minimal stdlib-only client: discover() + send_task()
```

This module **wraps, never reimplements** the four existing agents
(`agents/orchestrator/customer_intelligence_agent.py`, `agents/quality/data_quality_agent.py`,
`agents/recommendation/recommendation_agent.py`, `agents/monitoring/monitoring_agent.py`). Per
[ADR-014](../../docs/decisions/ADR-014-hexagonal-architecture.md), this is a third protocol
adapter around the same domain core that `mcp/tools/*.py` (MCP) and `api/services/*.py` (REST)
already expose — same capabilities, three different wire protocols.

## Design notes / documented spec deviations

The A2A spec assumes one agent per host (its own origin serving `/.well-known/agent.json` at the
root). This project hosts all four agents behind one local FastAPI process for a
testable-without-infrastructure Sprint 17 demo, so:
- each agent gets a path prefix instead of its own origin: `GET /agents/{agent_id}/.well-known/agent.json`
- `tasks/send` is a REST-style `POST /agents/{agent_id}/tasks/send`, not a single root JSON-RPC endpoint

A real multi-service deployment (e.g. one Pod per agent — see `../../k8s/`) could give each agent
its own origin and drop the path prefix without changing `agent_card.py`'s AgentCard content.

## Run it

```bash
uvicorn agents.a2a.server:app --port 8020
```

```bash
curl http://localhost:8020/agents
curl http://localhost:8020/agents/quality/.well-known/agent.json
curl -X POST http://localhost:8020/agents/quality/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"message":{"role":"user","parts":[{"type":"text","text":"silver.crm_customers"}]}}'
```

Or via the bundled client:

```bash
python -m agents.a2a.client http://localhost:8020 quality silver.crm_customers
```

## Verification — actually run for Sprint 17 (not simulated)

The server was booted locally (`uvicorn agents.a2a.server:app --port 8020`), each endpoint was
curled for real, and the server was stopped afterward. Exact commands and the exact JSON returned:

### `GET /agents/quality/.well-known/agent.json`

```json
{"protocolVersion":"0.2","name":"Data Quality Agent","description":"Diagnoses a data quality score drop for a given dataset: main cause (worst-scoring DQ dimension), affected row count, and a recommended action — never triggers a pipeline re-run itself. Wraps agents/quality/data_quality_agent.py:diagnose_quality_drop().","url":"http://127.0.0.1:8020/agents/quality","version":"0.1.0","provider":{"organization":"Enterprise Customer Intelligence Data Platform","url":"https://github.com"},"capabilities":{"streaming":false,"pushNotifications":false,"stateTransitionHistory":false},"defaultInputModes":["text/plain"],"defaultOutputModes":["application/json"],"skills":[{"id":"diagnose_quality_drop","name":"Diagnose a data quality drop","description":"Root-cause a DQ score drop for one dataset, per ARCHITECTURE.md §15's example format.","tags":["data-quality","diagnosis"],"examples":["Why did silver.crm_customers' DQ score drop?"]}]}
```

### `POST /agents/quality/tasks/send` — body `{"message":{"role":"user","parts":[{"type":"text","text":"silver.crm_customers"}]}}`

```json
{"id":"8e56368c-32f1-4564-b8fe-cd0addb1bf9e","sessionId":null,"status":{"state":"completed","timestamp":"2026-08-21T20:43:02.811946+00:00"},"artifacts":[{"name":"quality_result","parts":[{"type":"data","data":{"dataset":"silver.crm_customers","previous_score":null,"current_score":null,"main_cause":"unknown — no dimension scores available for silver.crm_customers yet","affected_rows":null,"recommended_action":"Inspect the GX Data Docs report for this dataset for the specific failing expectations.","text":"Quality decreased: unknown -> unknown\nMain cause: unknown — no dimension scores available for silver.crm_customers yet\nAffected rows: unknown\nRecommended action: Inspect the GX Data Docs report for this dataset for the specific failing expectations."}}]}]}
```

`current_score`/`main_cause` read as "unknown" because `mcp/tools/quality.py`'s
`get_data_quality()` is itself a documented stub returning `None` scores (Sprint 3's real GX
report wiring is out of this sprint's scope) — this is the wrapped agent's real, current behavior,
not something faked by the A2A layer.

### The other three agents were also sent real tasks in the same session (`orchestrator`, `recommendation`, `monitoring`) — all returned `"status":{"state":"completed"}` with each agent's actual current output (e.g. `recommendation` enqueued a real `PENDING` item in `approval_queue.py` with a live `queue_id`, `monitoring` returned `{"alerts":[],"alert_count":0}` since all thresholds are `None`-valued stubs per Sprint 16's TODO).

Server was then stopped (`Stop-Process`) and a follow-up `curl` to `/agents` was confirmed to fail
with a connection error, proving nothing was left running in the background.

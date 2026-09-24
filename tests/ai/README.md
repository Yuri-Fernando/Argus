# tests/ai/

Agent evaluation harnesses for `agents/`: Customer Intelligence, Data Quality, Recommendation,
Monitoring agents (LangGraph + human-in-the-loop, ROADMAP.md Sprint 14). Exercises the golden
question sets defined in `agents/*/evaluation/` (ARCHITECTURE.md §15) and the prompt-injection
test cases called out in that same section's "AI security" note.

**The human-in-the-loop acceptance criterion** — *"the Recommendation Agent's suggestion queue
requires explicit approval before any downstream action is logged as `executed`"*, i.e. that
ADR-006's gate cannot be bypassed by any agent path, adversarial prompt included — is proved in
[`agents/orchestrator/tests/test_human_in_the_loop.py`](../../agents/orchestrator/tests/test_human_in_the_loop.py)
rather than here, since it needs the real compiled LangGraph graph (its own module-level
singleton, `InMemorySaver` checkpointer included) as a fixture, not just this directory's
evaluation-harness pattern. 6 tests, no LLM/network call: pause on a policy question, approve,
reject, **forge an approval in the resume payload without ever calling `approve()`** (still
blocked — the sharpest version of the guarantee), and the queue's own `mark_executed()` guard.

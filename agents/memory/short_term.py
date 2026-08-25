"""Short-term (conversation-scoped) memory — a LangGraph checkpointer-based buffer.

Built per ADR-013, addressing add2.txt's "agentes conversacionais com memória de curto ... prazo."
Scoped per conversation thread: this is the message-window context a single conversation needs
(the last N turns), not durable across sessions — that's `long_term.py`'s job.

Backs `agents/orchestrator/customer_intelligence_agent.py`'s multi-turn use (a customer asking a
follow-up question in the same session) without changing that graph's existing node contract —
this module supplies the checkpointer `StateGraph.compile(checkpointer=...)` accepts, it does not
modify the compiled graph in orchestrator/customer_intelligence_agent.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ConversationTurn:
    """One exchange within a conversation thread — the unit short-term memory stores."""

    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """Per-thread conversation buffer, bounded to the last `max_turns` exchanges.

    Wraps the same role LangGraph's built-in checkpointers (e.g. `MemorySaver` for local dev,
    a Postgres-backed checkpointer in production) play: giving a `thread_id`-scoped agent access
    to recent conversation state without re-sending the full history as part of `AgentState` on
    every node call.
    """

    def __init__(self, *, max_turns: int = 20) -> None:
        """
        Args:
            max_turns: maximum turns retained per thread — bounds both LLM context size and
                memory footprint; oldest turns are dropped first (FIFO), never silently truncated
                mid-turn.
        """
        self.max_turns = max_turns
        self._threads: dict[str, list[ConversationTurn]] = {}

    def append(self, thread_id: str, turn: ConversationTurn) -> None:
        """Add a turn to a thread's buffer, evicting the oldest turn if `max_turns` is exceeded.

        Args:
            thread_id: conversation/session identifier — typically a UUID minted when a customer
                or support agent opens a chat session with the Customer Intelligence Agent.
            turn: the exchange to record.
        """
        buffer = self._threads.setdefault(thread_id, [])
        buffer.append(turn)
        if len(buffer) > self.max_turns:
            del buffer[0 : len(buffer) - self.max_turns]

    def get_recent(self, thread_id: str, *, limit: int | None = None) -> list[ConversationTurn]:
        """Return the most recent turns for a thread, oldest-first.

        Args:
            thread_id: conversation/session identifier.
            limit: optional cap smaller than the buffer's `max_turns`, e.g. to fit a tighter
                prompt budget for a cheap `task_type` routed via `agents/llm_gateway/router.py`.
        """
        buffer = self._threads.get(thread_id, [])
        if limit is None:
            return list(buffer)
        return buffer[-limit:]

    def clear(self, thread_id: str) -> None:
        """Drop a thread's buffer entirely — called when a conversation session ends normally.

        Note this is distinct from the LGPD-driven deletion path: short-term memory is process-
        local and already ephemeral by design (see README "Traceability" section); the durable,
        attributable record lives in `long_term.py`, which is what an Art. 18 IV erasure request
        actually needs to reach.
        """
        self._threads.pop(thread_id, None)


# Module-level default instance, mirroring the pattern `agents/recommendation/approval_queue.py`
# uses for its shared in-memory queue — swap for a real LangGraph checkpointer (MemorySaver
# locally, a Postgres-backed checkpointer in production) once Sprint 14's LangGraph wiring lands.
_default_memory = ShortTermMemory()


def get_short_term_memory() -> ShortTermMemory:
    """Return the shared default ShortTermMemory instance."""
    return _default_memory

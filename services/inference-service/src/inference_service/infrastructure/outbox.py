"""Transactional Outbox (ADR-022).

Problema: publicar um evento direto no broker depois de commitar no banco
abre uma janela de falha — se o processo cai entre o commit e o publish, o
evento se perde. Solução: gravar o evento numa tabela `outbox` na MESMA
transação do banco; um relay assíncrono lê a tabela e publica no broker,
marcando como enviado. Entrega passa a ser at-least-once garantida.

Aqui o "banco" é SQLite (arquivo local) — o mesmo padrão vale para o
Postgres do serviço em produção.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from inference_service.application.ports import EventPublisher
from inference_service.domain.events import PredictionMade

_SCHEMA = """
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT
);
"""


class SqliteOutbox:
    def __init__(self, db_path: str | Path = "outbox.db"):
        self.db_path = str(db_path)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def append(self, topic: str, payload: dict) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO outbox (topic, payload, created_at) VALUES (?, ?, ?)",
                (topic, json.dumps(payload), datetime.now(timezone.utc).isoformat()),
            )
            return int(cur.lastrowid)

    def pending(self) -> list[sqlite3.Row]:
        with self._conn() as c:
            return list(c.execute("SELECT * FROM outbox WHERE published_at IS NULL ORDER BY id"))

    def mark_published(self, row_id: int) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE outbox SET published_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), row_id),
            )

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
            pending = c.execute("SELECT COUNT(*) FROM outbox WHERE published_at IS NULL").fetchone()[0]
        return {"total": total, "pending": pending, "published": total - pending}


class OutboxEventPublisher(EventPublisher):
    """Implementação do port `EventPublisher` que grava no outbox em vez de
    publicar direto — durabilidade garantida antes de qualquer broker."""

    TOPIC = "model.prediction.created"

    def __init__(self, outbox: SqliteOutbox):
        self._outbox = outbox

    def publish(self, event: PredictionMade) -> None:
        self._outbox.append(self.TOPIC, event.to_message())


def relay(outbox: SqliteOutbox, bus, limit: int | None = None) -> int:
    """Drena o outbox para o `bus` real (InMemoryBus/KafkaBus). Idempotente:
    só publica linhas ainda não marcadas. Retorna quantas publicou."""
    published = 0
    for row in outbox.pending():
        if limit is not None and published >= limit:
            break
        bus.publish(row["topic"], json.loads(row["payload"]))
        outbox.mark_published(row["id"])
        published += 1
    return published

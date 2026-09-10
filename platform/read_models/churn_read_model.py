"""Read model CQRS (ADR-022, RFC-002).

O lado de escrita publica domain events em `model.prediction.created` e
`customer.updated`. Este read model consome esses eventos e materializa, em
SQLite, tabelas desnormalizadas prontas para o dashboard:

- `customer_360(customer_id, last_score, high_risk, updates, last_seen)`
- `churn_kpis(key, value)`  — agregados globais

Propriedade central de CQRS/event-sourcing: o read model é **reconstruível**
por replay do log de eventos — `rebuild_from_events()` produz exatamente o
mesmo estado que o consumo incremental.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS customer_360 (
    customer_id TEXT PRIMARY KEY,
    last_score REAL,
    high_risk INTEGER DEFAULT 0,
    updates INTEGER DEFAULT 0,
    last_seen TEXT
);
CREATE TABLE IF NOT EXISTS churn_kpis (key TEXT PRIMARY KEY, value REAL);
"""


class ChurnReadModel:
    def __init__(self, db_path: str | Path = ":memory:"):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    # --- projeções (um handler por tipo de evento) --------------------------

    def on_prediction_created(self, e: dict) -> None:
        cid = e["model_id"].split("@")[0] if "@" in e.get("model_id", "") else e.get("request_id", "")
        cid = e.get("customer_id", cid)
        high = 1 if e.get("high_risk") else 0
        self._conn.execute(
            """
            INSERT INTO customer_360 (customer_id, last_score, high_risk, updates, last_seen)
            VALUES (:cid, :score, :high, 1, :ts)
            ON CONFLICT(customer_id) DO UPDATE SET
                last_score = :score, high_risk = :high,
                updates = customer_360.updates + 1, last_seen = :ts
            """,
            {"cid": cid, "score": e.get("score"), "high": high, "ts": e.get("occurred_at")},
        )
        self._recompute_kpis()

    def on_customer_updated(self, e: dict) -> None:
        self._conn.execute(
            """
            INSERT INTO customer_360 (customer_id, updates, last_seen)
            VALUES (:cid, 1, :ts)
            ON CONFLICT(customer_id) DO UPDATE SET
                updates = customer_360.updates + 1, last_seen = :ts
            """,
            {"cid": e["customer_id"], "ts": e.get("occurred_at")},
        )

    def _recompute_kpis(self) -> None:
        row = self._conn.execute(
            "SELECT COUNT(*) n, COALESCE(AVG(last_score),0) avg_s, "
            "COALESCE(SUM(high_risk),0) hr FROM customer_360 WHERE last_score IS NOT NULL"
        ).fetchone()
        for k, v in (("scored_customers", row["n"]), ("avg_score", round(row["avg_s"], 4)),
                     ("high_risk_count", row["hr"])):
            self._conn.execute(
                "INSERT INTO churn_kpis (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (k, v),
            )
        self._conn.commit()

    # --- API de leitura (o que o dashboard consome) -----------------------

    def customer(self, customer_id: str) -> dict | None:
        r = self._conn.execute("SELECT * FROM customer_360 WHERE customer_id = ?", (customer_id,)).fetchone()
        return dict(r) if r else None

    def kpis(self) -> dict:
        return {r["key"]: r["value"] for r in self._conn.execute("SELECT * FROM churn_kpis")}

    def dump(self) -> dict:
        return {
            "customer_360": [dict(r) for r in self._conn.execute("SELECT * FROM customer_360 ORDER BY customer_id")],
            "churn_kpis": self.kpis(),
        }

    # --- wiring + replay --------------------------------------------------

    def subscribe_to(self, bus) -> None:
        bus.subscribe("model.prediction.created", self.on_prediction_created)
        bus.subscribe("customer.updated", self.on_customer_updated)

    def rebuild_from_events(self, events: list[tuple[str, dict]]) -> "ChurnReadModel":
        """Replay: `[(topic, payload), ...]` na ordem do log."""
        for topic, payload in events:
            if topic == "model.prediction.created":
                self.on_prediction_created(payload)
            elif topic == "customer.updated":
                self.on_customer_updated(payload)
        return self

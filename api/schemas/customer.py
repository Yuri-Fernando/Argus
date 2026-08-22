"""Pydantic request/response models for the `/customer` route group.

Field shapes mirror `mdm/golden_record/` (canonical name/email/phone/city/state) and
`ml/features/` + `ml/segmentation/` (churn/segment) so the REST contract matches what those
modules actually produce on disk — no invented fields, per Constitution Article IV.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CustomerCreateRequest(BaseModel):
    """Body for `POST /customer` — registers a new (unresolved) customer record.

    This is intentionally the shape of a single source-system record, not a Golden Record: MDM
    survivorship (`mdm/golden_record/`) is what turns one-or-more of these into a Golden Record
    later. `POST /customer` only appends to the intake queue this API layer owns.
    """

    name: str = Field(..., min_length=1, max_length=200)
    # Plain `str` with a permissive regex, not pydantic's `EmailStr` — that requires the optional
    # `email-validator` package, which isn't installed and this task's scope forbids adding
    # dependencies. The regex still rejects an obviously malformed value.
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(..., min_length=8, max_length=20)
    city: str | None = None
    state: str | None = None


class CustomerCreateResponse(BaseModel):
    """Response for `POST /customer`."""

    source_customer_id: str
    name: str
    email: str
    phone: str
    city: str | None
    state: str | None
    registered_at: datetime


class GoldenRecordResponse(BaseModel):
    """Response for `GET /customer/{id}` — a Golden Record view from `mdm/golden_record/`."""

    master_customer_id: str
    canonical_name: str | None
    canonical_email: str | None
    canonical_phone: str | None
    city: str | None
    state: str | None
    source_record_count: int | None
    created_at: datetime | None
    updated_at: datetime | None
    found: bool


class ChurnScoreResponse(BaseModel):
    """Response for `GET /customer/score` — churn score + segment for one customer.

    `churn_score` uses the same recency-based proxy formula as
    `snowflake/local_runner.py::build_warehouse` (no `ml/churn/` model output parquet exists in
    this snapshot — documented deviation, see that module's docstring), so this endpoint's number
    is consistent with what `GET /metrics` derives its churn_rate from.
    """

    master_customer_id: str
    found: bool
    churn_score: float | None = None
    segment: str | None = None
    cluster: int | None = None
    recency_days: int | None = None
    frequency: int | None = None
    monetary: float | None = None


class DuplicatePair(BaseModel):
    """One MDM candidate/confirmed duplicate pair, from `mdm/matching/`."""

    id_1: str
    id_2: str
    decision: str
    n_keys: int | None = None
    match_probability: float | None = None
    strong: bool | None = None
    tier: str | None = None


class DuplicatesResponse(BaseModel):
    """Response for `GET /customer/duplicates`."""

    total: int
    returned: int
    pairs: list[DuplicatePair]

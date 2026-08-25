"""`/customer` route group — see `api/README.md`'s route table for what this mirrors in `mcp/`."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas.customer import (
    ChurnScoreResponse,
    CustomerCreateRequest,
    CustomerCreateResponse,
    DuplicatesResponse,
    GoldenRecordResponse,
)
from api.services import customer_service

router = APIRouter(prefix="/customer", tags=["customer"])


@router.post("", response_model=CustomerCreateResponse, status_code=201)
def create_customer(payload: CustomerCreateRequest) -> CustomerCreateResponse:
    """Register a new source-system customer record (pre-MDM-resolution intake)."""
    record = customer_service.register_customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        city=payload.city,
        state=payload.state,
    )
    return CustomerCreateResponse(**record)


@router.get("/score", response_model=ChurnScoreResponse)
def get_customer_score(
    master_customer_id: str = Query(..., description="MDM-assigned Golden Record id, e.g. MC00000001"),
) -> ChurnScoreResponse:
    """Churn score + segment for one customer, from `ml/features/` + `ml/segmentation/`."""
    result = customer_service.get_churn_score(master_customer_id)
    return ChurnScoreResponse(**result)


@router.get("/duplicates", response_model=DuplicatesResponse)
def get_customer_duplicates(
    decision: str | None = Query(
        None, description="Filter by decision, e.g. AUTO_MATCH (confirmed) or PENDING_FUZZY_ML (candidate)"
    ),
    limit: int = Query(50, ge=1, le=200),
) -> DuplicatesResponse:
    """MDM candidate/confirmed duplicate pairs, from `mdm/matching/`."""
    result = customer_service.get_duplicate_pairs(decision=decision, limit=limit)
    return DuplicatesResponse(**result)


@router.get("/{master_customer_id}", response_model=GoldenRecordResponse)
def get_customer(master_customer_id: str) -> GoldenRecordResponse:
    """Golden Record view for one customer, from `mdm/golden_record/`."""
    result = customer_service.get_golden_record(master_customer_id)
    if not result["found"]:
        raise HTTPException(status_code=404, detail=f"No Golden Record for {master_customer_id!r}")
    return GoldenRecordResponse(**result)

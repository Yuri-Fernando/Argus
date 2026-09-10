"""Interface REST (FastAPI) do Inference Service.

Camada fina: valida o request, chama o use case, serializa a resposta.
Nenhuma regra de domínio aqui.
"""
from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from inference_service.application.predict import PredictUseCase
from inference_service.domain.model import InferenceRequest, ModelId
from inference_service.infrastructure.in_memory_event_bus import InMemoryEventBus
from inference_service.infrastructure.model_factory import ModelFactory


class PredictBody(BaseModel):
    model_name: str = Field(..., examples=["churn"])
    model_version: str = Field("1", examples=["1"])
    request_id: str = Field(..., examples=["req-001"])
    features: dict[str, float | int | str]


class PredictResponse(BaseModel):
    model_id: str
    request_id: str
    score: float
    label: str
    high_risk: bool
    explanation: dict


def build_router(use_case: PredictUseCase) -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["inference"])

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.post("/predict", response_model=PredictResponse)
    def predict(body: PredictBody) -> PredictResponse:
        try:
            request = InferenceRequest(
                model_id=ModelId(body.model_name, body.model_version),
                features=body.features,
                request_id=body.request_id,
            )
            prediction = use_case.execute(request)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return PredictResponse(
            model_id=str(prediction.model_id),
            request_id=prediction.request_id,
            score=prediction.score,
            label=prediction.label,
            high_risk=prediction.is_high_risk,
            explanation=prediction.explanation,
        )

    return router


def create_app() -> FastAPI:
    """Composition root — monta o grafo de dependências (Factory + bus + use case)."""
    factory = ModelFactory()
    bus = InMemoryEventBus()
    use_case = PredictUseCase(resolver=factory, event_publisher=bus)

    app = FastAPI(title="Argus — Inference Service", version="0.1.0")
    app.include_router(build_router(use_case))
    app.state.event_bus = bus
    return app


app = create_app()

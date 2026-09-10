"""Interface gRPC do inference-service (ADR-021).

Mesma camada fina que a REST: converte o request do protobuf, chama o
`PredictUseCase`, serializa a resposta. Nenhuma regra de domínio aqui. O
mesmo composition root (Factory + bus + use case) serve as duas interfaces.
"""
from __future__ import annotations

import json
from concurrent import futures

import grpc

from inference_service.application.predict import PredictUseCase
from inference_service.domain.model import InferenceRequest, ModelId
from inference_service.infrastructure.in_memory_event_bus import InMemoryEventBus
from inference_service.infrastructure.model_factory import ModelFactory
from inference_service.interfaces.grpc_gen import inference_pb2, inference_pb2_grpc


class InferenceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def __init__(self, use_case: PredictUseCase):
        self._use_case = use_case

    def Predict(self, request, context):
        try:
            inf_request = InferenceRequest(
                model_id=ModelId(request.model_name, request.model_version or "1"),
                features={k: float(v) for k, v in request.features.items()},
                request_id=request.request_id,
            )
            prediction = self._use_case.execute(inf_request)
        except (KeyError, ValueError) as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            return inference_pb2.PredictResponse()

        return inference_pb2.PredictResponse(
            model_id=str(prediction.model_id),
            request_id=prediction.request_id,
            score=prediction.score,
            label=prediction.label,
            high_risk=prediction.is_high_risk,
            explanation_json=json.dumps(prediction.explanation),
        )

    def Health(self, request, context):
        return inference_pb2.HealthResponse(status="ok")


def build_servicer() -> InferenceServicer:
    """Composition root — mesmo grafo de dependências da interface REST."""
    factory = ModelFactory()
    bus = InMemoryEventBus()
    use_case = PredictUseCase(resolver=factory, event_publisher=bus)
    return InferenceServicer(use_case)


def serve(port: int = 50051) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(build_servicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server


if __name__ == "__main__":
    srv = serve()
    print("inference-service gRPC em :50051")
    srv.wait_for_termination()

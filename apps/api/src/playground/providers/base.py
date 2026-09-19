from dataclasses import dataclass
from typing import Protocol

from playground.decision import Decision
from playground.schemas import ProviderInfo


class ProviderError(Exception):
    def __init__(self, code: str, message: str, status: int = 503):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class Prediction:
    choice: str
    probabilities: dict[str, float]
    model: str
    device: str
    model_revision: str | None = None
    input_tokens: int | None = None
    model_load_ms: float = 0
    inference_ms: float = 0


class DecisionProvider(Protocol):
    def info(self) -> ProviderInfo: ...

    def predict(self, decision: Decision) -> Prediction: ...

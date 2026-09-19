from time import perf_counter

import httpx

from playground.config import Settings
from playground.decision import Decision
from playground.providers.base import Prediction, ProviderError
from playground.schemas import ProviderInfo


class JevProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def info(self) -> ProviderInfo:
        available = bool(self.settings.jev_api_key.get_secret_value())
        return ProviderInfo(
            id="jev",
            name="TypeSafe Jev",
            model=self.settings.jev_model,
            available=available,
            loaded=available,
            device="remote",
            reason=None if available else "尚未設定 JEV_API_KEY",
        )

    def predict(self, decision: Decision) -> Prediction:
        if not self.info().available:
            raise ProviderError("provider_unavailable", "請先在 .env 設定 JEV_API_KEY")
        started = perf_counter()
        try:
            response = httpx.post(
                self.settings.jev_api_url,
                headers={"Authorization": f"Bearer {self.settings.jev_api_key.get_secret_value()}"},
                json={
                    "model": self.settings.jev_model,
                    "state": decision.state,
                    "questions": decision.questions,
                },
                timeout=httpx.Timeout(60, connect=10),
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError("provider_timeout", "Jev 回應逾時，請稍後再試", 504) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                "upstream_error", f"Jev 回傳 HTTP {exc.response.status_code}", 502
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError("upstream_error", "無法連線到 Jev", 502) from exc
        elapsed = (perf_counter() - started) * 1000
        try:
            data = response.json()
            answer = data["answers"]["recommendation"]
            return Prediction(
                choice=answer["choice"],
                probabilities=answer["probabilities"],
                model=data["model"],
                device="remote",
                inference_ms=elapsed,
                input_tokens=data.get("usage", {}).get("input_tokens"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("invalid_response", "Jev 回應格式不符預期", 502) from exc

import math
from time import perf_counter
from uuid import uuid4

from playground.decision import PROMPT_VERSION, build_decision
from playground.providers.base import DecisionProvider, ProviderError
from playground.schemas import (
    Catalog,
    Metadata,
    OptionResult,
    ProviderId,
    RecommendationRequest,
    RecommendationResponse,
    Timing,
)


class RecommendationService:
    def __init__(self, catalog: Catalog, providers: dict[ProviderId, DecisionProvider]):
        self.catalog = catalog
        self.providers = providers

    def metadata(self) -> Metadata:
        return Metadata(catalog=self.catalog, providers=[p.info() for p in self.providers.values()])

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        started = perf_counter()
        decision = build_decision(request.question, self.catalog)
        result = self.providers[request.provider].predict(decision)
        probabilities = result.probabilities
        # Preserve model probabilities, including upstream rounding; never invent a none score.
        if (
            not isinstance(probabilities, dict)
            or not isinstance(result.choice, str)
            or set(probabilities) != set(decision.criteria)
            or any(
                isinstance(p, bool)
                or not isinstance(p, (int, float))
                or not math.isfinite(p)
                or not 0 <= p <= 1
                for p in probabilities.values()
            )
            or abs(sum(probabilities.values()) - 1) > 0.005
            or result.choice not in probabilities
            or probabilities[result.choice] < max(probabilities.values())
        ):
            raise ProviderError("invalid_distribution", "模型回傳不完整或無效的選項機率", 502)
        options = [
            OptionResult(
                id=a.id,
                title=a.title,
                url=a.url,
                summary=a.summary,
                category=a.category,
                probability=probabilities[a.id],
                is_none=False,
            )
            for a in self.catalog.articles
        ]
        options.append(
            OptionResult(
                id="none",
                title="沒有可推薦的",
                url=None,
                summary="目前文章中，沒有能直接幫助回答這個問題的內容。",
                category="不推薦",
                probability=probabilities["none"],
                is_none=True,
            )
        )
        options.sort(key=lambda option: option.probability, reverse=True)
        return RecommendationResponse(
            request_id=str(uuid4()),
            question=request.question,
            provider=request.provider,
            model=result.model,
            model_revision=result.model_revision,
            device=result.device,
            recommended_id=result.choice,
            options=options,
            timing=Timing(
                model_load_ms=round(result.model_load_ms, 2),
                inference_ms=round(result.inference_ms, 2),
                server_total_ms=round((perf_counter() - started) * 1000, 2),
            ),
            input_tokens=result.input_tokens,
            catalog_version=self.catalog.fetched_at,
            prompt_version=PROMPT_VERSION,
        )

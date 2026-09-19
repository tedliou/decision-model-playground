from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ProviderId = Literal["laya", "jev"]


class Article(BaseModel):
    id: str
    title: str
    url: str
    summary: str
    category: str
    decision_label: str


class Catalog(BaseModel):
    source: str
    fetched_at: str
    articles: list[Article]


class ProviderInfo(BaseModel):
    id: ProviderId
    name: str
    model: str
    available: bool
    loaded: bool
    reason: str | None = None
    device: str | None = None


class Metadata(BaseModel):
    catalog: Catalog
    providers: list[ProviderInfo]


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=500)
    provider: ProviderId = "laya"

    @field_validator("question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("請輸入問題")
        return value


class OptionResult(BaseModel):
    id: str
    title: str
    url: str | None
    summary: str
    category: str
    probability: float = Field(ge=0, le=1)
    is_none: bool


class Timing(BaseModel):
    model_load_ms: float
    inference_ms: float
    server_total_ms: float


class RecommendationResponse(BaseModel):
    request_id: str
    question: str
    provider: ProviderId
    model: str
    model_revision: str | None
    device: str
    recommended_id: str
    options: list[OptionResult]
    timing: Timing
    input_tokens: int | None
    catalog_version: str
    prompt_version: str
    probability_kind: Literal["categorical_choice"] = "categorical_choice"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

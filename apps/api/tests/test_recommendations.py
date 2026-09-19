from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient
from playground.catalog import load_catalog
from playground.config import Settings
from playground.decision import build_decision
from playground.main import create_app
from playground.providers.base import Prediction, ProviderError
from playground.providers.jev import JevProvider
from playground.schemas import ProviderInfo
from playground.service import RecommendationService


class StubProvider:
    def __init__(self, prediction):
        self.prediction = prediction
        self.decisions = []

    def info(self):
        return ProviderInfo(id="laya", name="test", model="test", available=True, loaded=True)

    def predict(self, decision):
        self.decisions.append(decision)
        return self.prediction


@pytest.fixture
def setup():
    catalog = load_catalog()
    probabilities = {article.id: 0 for article in catalog.articles}
    probabilities.update(a03=0.25, none=0.75)
    prediction = Prediction(choice="none", probabilities=probabilities, model="test", device="cpu")
    provider = StubProvider(prediction)
    client = TestClient(
        create_app(RecommendationService(catalog, {"laya": provider, "jev": provider}))
    )
    return client, provider


def test_none_is_a_real_winner_and_all_probabilities_are_preserved(setup):
    client, provider = setup
    response = client.post("/api/v1/recommendations", json={"question": "  有推薦嗎？  "})
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "有推薦嗎？"
    assert body["recommended_id"] == "none"
    assert len(body["options"]) == 19
    assert body["options"][0]["url"] is None
    assert {o["id"]: o["probability"] for o in body["options"]} == provider.prediction.probabilities
    assert body["timing"]["server_total_ms"] >= 0


def test_provider_switch_receives_identical_decision(setup):
    client, provider = setup
    for model in ("laya", "jev"):
        assert (
            client.post(
                "/api/v1/recommendations",
                json={
                    "question": "TouchDesigner",
                    "provider": model,
                },
            ).status_code
            == 200
        )
    assert provider.decisions[0] == provider.decisions[1]


@pytest.mark.parametrize(
    "body",
    [
        {"question": " "},
        {"question": "x" * 501},
        {"question": "hi", "provider": "unknown"},
        {"question": "hi", "api_key": "should not be here"},
        {},
    ],
)
def test_invalid_requests_have_consistent_errors(setup, body):
    response = setup[0].post("/api/v1/recommendations", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    "bad",
    [
        {"none": 1.0},
        {"none": float("nan")},
        {"none": -0.1},
        {"none": 0.1},
    ],
)
def test_invalid_model_distributions_are_rejected(setup, bad):
    client, provider = setup
    probabilities = dict(provider.prediction.probabilities)
    probabilities.update(bad)
    provider.prediction = replace(provider.prediction, probabilities=probabilities)
    response = client.post("/api/v1/recommendations", json={"question": "hi"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_distribution"


def test_missing_option_rejected(setup):
    client, provider = setup
    provider.prediction = replace(provider.prediction, probabilities={"none": 1})
    assert client.post("/api/v1/recommendations", json={"question": "hi"}).status_code == 502


def test_missing_jev_key_is_not_exposed():
    provider = JevProvider(Settings(jev_api_key=""))
    assert provider.info().available is False
    with pytest.raises(ProviderError, match="JEV_API_KEY"):
        provider.predict(build_decision("hello", load_catalog()))


def test_jev_adapter_contract(monkeypatch):
    decision = build_decision("TouchDesigner", load_catalog())
    probabilities = {key: int(key == "a03") for key in decision.criteria}

    def post(url, **kwargs):
        assert url == "https://api.typesafe.ai/v1/systemone"
        assert kwargs["headers"]["Authorization"] == "Bearer fake-test-key"
        assert kwargs["json"]["state"] == decision.state
        assert kwargs["json"]["questions"] == decision.questions
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "model": "jev-test",
                "answers": {
                    "recommendation": {
                        "choice": "a03",
                        "probabilities": probabilities,
                    }
                },
                "usage": {"input_tokens": 300},
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    result = JevProvider(Settings(jev_api_key="fake-test-key")).predict(decision)
    assert result.choice == "a03"
    assert result.probabilities == probabilities
    assert result.model == "jev-test"


@pytest.mark.parametrize("status", [401, 429, 500])
def test_jev_errors_do_not_leak_upstream_body_or_key(monkeypatch, status):
    def post(url, **_kwargs):
        return httpx.Response(
            status, request=httpx.Request("POST", url), text="secret upstream body"
        )

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(ProviderError) as error:
        JevProvider(Settings(jev_api_key="fake-test-key")).predict(
            build_decision("hi", load_catalog())
        )
    assert error.value.status == 502
    assert "secret" not in error.value.message


def test_metadata_has_no_credentials(setup):
    body = setup[0].get("/api/v1/metadata").json()
    assert len(body["catalog"]["articles"]) == 18
    assert "api_key" not in str(body).lower()

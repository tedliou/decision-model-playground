import json
import os
from threading import Lock
from time import perf_counter

from playground.config import Settings, configure_runtime
from playground.decision import Decision
from playground.providers.base import Prediction, ProviderError
from playground.schemas import ProviderInfo

REQUIRED_FILES = (
    "model.safetensors",
    "rl_agent_config.json",
    "encoder/config.json",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json",
    "provenance.json",
)


class LayaProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._agent = None
        self._lock = Lock()
        self._revision = None

    def info(self) -> ProviderInfo:
        available = all((self.settings.model_path / file).is_file() for file in REQUIRED_FILES)
        return ProviderInfo(
            id="laya",
            name="Laya Multilingual",
            model="convaiinnovations/laya-multilingual",
            available=available,
            loaded=self._agent is not None,
            device=str(self._agent.device) if self._agent else self.settings.laya_device,
            reason=None if available else "請先執行 npm run model:download",
        )

    def _load(self) -> float:
        if self._agent is not None:
            return 0
        if not self.info().available:
            raise ProviderError("model_missing", "模型尚未下載，請執行 npm run model:download")
        configure_runtime()
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        started = perf_counter()
        import laya
        import torch

        if self.settings.laya_device == "cuda" and not torch.cuda.is_available():
            raise ProviderError("device_unavailable", "CUDA 無法使用；請檢查 PyTorch 與顯示卡驅動")
        agent = laya.load(str(self.settings.model_path), device=self.settings.laya_device)
        if str(agent.device) != self.settings.laya_device:
            raise ProviderError("device_changed", "模型未載入指定裝置，請檢查 GPU 記憶體")
        self._revision = json.loads(
            (self.settings.model_path / "provenance.json").read_text("utf-8")
        )["revision"]
        self._agent = agent
        return (perf_counter() - started) * 1000

    def _validate_budget(self, decision: Decision) -> int:
        """Reject any input the upstream formatter would silently truncate."""
        from laya.common import render_options

        agent = self._agent
        q = agent._to_internal(decision.questions["recommendation"])
        tok = agent.tok

        def tokens(text: str) -> int:
            return len(
                tok(text.replace(tok.mask_token, " "), add_special_tokens=False)["input_ids"]
            )

        options = [tokens(" " + text) for text in render_options(q)]
        head = tokens(f"choice question: {q['ins']}")
        option_total = sum(size + 1 for size in options)
        head_max = agent.cfg["head_max_len"]
        if max(options) > 48 or head_max - option_total < max(16, head):
            raise ProviderError(
                "option_budget_exceeded", "文章選項超過 Laya 的完整讀取上限，請縮短模型用描述", 422
            )
        length = 4 + head + option_total + tokens(decision.state)
        if length > agent.cfg["max_len"]:
            raise ProviderError(
                "context_exceeded",
                f"輸入需要 {length} tokens，超過 Laya 的 {agent.cfg['max_len']} 上限；請縮短問題",
                422,
            )
        return length

    def predict(self, decision: Decision) -> Prediction:
        # One resident model, one GPU job. Do not silently queue concurrent experiments.
        if not self._lock.acquire(blocking=False):
            raise ProviderError("model_busy", "Laya 正在處理另一個問題，請稍後再試", 409)
        try:
            load_ms = self._load()
            self._validate_budget(decision)
            import torch

            if self._agent.device.type == "cuda":
                torch.cuda.synchronize()
            started = perf_counter()
            result = self._agent.predict(decision.state, decision.questions)
            if str(self._agent.device) != self.settings.laya_device:
                self._agent = None
                raise ProviderError("device_changed", "推論未使用指定裝置，請檢查 GPU 記憶體")
            if self._agent.device.type == "cuda":
                torch.cuda.synchronize()
            elapsed = (perf_counter() - started) * 1000
            answer = result["answers"]["recommendation"]
            return Prediction(
                choice=answer["choice"],
                probabilities=answer["probabilities"],
                model="convaiinnovations/laya-multilingual",
                model_revision=self._revision,
                device=str(self._agent.device),
                input_tokens=result["usage"]["input_tokens"],
                model_load_ms=load_ms,
                inference_ms=elapsed,
            )
        finally:
            self._lock.release()

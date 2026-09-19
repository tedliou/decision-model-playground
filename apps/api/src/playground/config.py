import os
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    laya_model_path: str = "models/laya-multilingual"
    laya_device: str = "cuda"
    jev_api_key: SecretStr = SecretStr("")
    jev_model: str = "jev-1.13.0"
    jev_api_url: str = "https://api.typesafe.ai/v1/systemone"

    @property
    def model_path(self) -> Path:
        path = (ROOT / self.laya_model_path).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("LAYA_MODEL_PATH must stay inside the workspace")
        return path


def configure_runtime() -> None:
    # Set before importing torch/transformers/huggingface_hub. No global model caches.
    os.environ["HF_HOME"] = str(ROOT / ".cache/huggingface")
    os.environ["TORCH_HOME"] = str(ROOT / ".cache/torch")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["USE_TF"] = "0"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

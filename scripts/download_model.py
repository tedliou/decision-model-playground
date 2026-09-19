"""Download one immutable model revision into this workspace; never into global caches."""

import json
from datetime import UTC, datetime

from playground.config import ROOT, Settings, configure_runtime

configure_runtime()

from huggingface_hub import snapshot_download  # noqa: E402


def main() -> None:
    path = Settings().model_path
    manifest_path = path / "provenance.json"
    lock = json.loads((ROOT / "data/model.json").read_text("utf-8"))
    repo, revision = lock["repository"], lock["revision"]
    snapshot_download(
        repo,
        revision=revision,
        local_dir=path,
        allow_patterns=[
            "model.safetensors",
            "rl_agent_config.json",
            "encoder/*",
            "tokenizer/*",
            "README.md",
            "LICENSE*",
        ],
    )
    manifest_path.write_text(
        json.dumps(
            {
                "repository": repo,
                "revision": revision,
                "downloaded_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Model ready: {path}\nRevision: {revision}")


if __name__ == "__main__":
    main()

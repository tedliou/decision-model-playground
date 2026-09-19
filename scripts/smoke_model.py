"""Run real, labelled examples; report model quality without asserting it is always correct."""

import json
from datetime import UTC, datetime

from playground.config import ROOT
from playground.main import app
from playground.schemas import RecommendationRequest

CASES = [
    ("我想讓 AI 幫我操作 TouchDesigner", "a03"),
    ("Astro 網站每次部署都要很久，怎麼加速？", "a01"),
    ("如何讓 Unity 使用 VS Code 寫 C#？", "a12"),
    ("怎麼煮出好吃的義大利麵？", "none"),
]


def main():
    results = []
    for question, expected in CASES:
        result = app.state.service.recommend(RecommendationRequest(question=question))
        row = {
            "expected": expected,
            "correct": result.recommended_id == expected,
            **result.model_dump(),
        }
        results.append(row)
        print(
            json.dumps(
                {
                    "question": question,
                    "expected": expected,
                    "actual": result.recommended_id,
                    "timing": result.timing.model_dump(),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    out = ROOT / ".logs/smoke-model.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        json.dumps(
            {"run_at": datetime.now(UTC).isoformat(), "cases": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved {out}")


if __name__ == "__main__":
    main()

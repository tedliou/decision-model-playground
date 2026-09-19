import json

from playground.config import ROOT
from playground.main import app

(ROOT / "apps/api/openapi.json").write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

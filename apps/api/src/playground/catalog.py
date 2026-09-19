from playground.config import ROOT
from playground.schemas import Catalog


def load_catalog() -> Catalog:
    catalog = Catalog.model_validate_json((ROOT / "data/articles.json").read_text("utf-8"))
    ids = [article.id for article in catalog.articles]
    if not ids or len(ids) != len(set(ids)) or "none" in ids:
        raise ValueError("Article IDs must be nonempty, unique and not 'none'")
    if len(ids) > 19:
        raise ValueError("This experiment supports at most 19 articles plus 'none'")
    return catalog

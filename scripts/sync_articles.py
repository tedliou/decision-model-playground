"""Refresh published metadata, requiring reviewed compact descriptors for every article."""

import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx
from playground.config import ROOT

SOURCE = "https://vervecode.dev/index.xml"


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def main() -> None:
    descriptors = json.loads((ROOT / "data/descriptors.json").read_text("utf-8"))
    response = httpx.get(SOURCE, timeout=30)
    response.raise_for_status()
    articles = []
    for item in ElementTree.fromstring(response.content).findall("./channel/item"):
        url = item.findtext("link")
        path = urlparse(url).path
        if path not in descriptors:
            raise SystemExit(f"Add a reviewed description in data/descriptors.json for {path}")
        plain = PlainText()
        plain.feed(item.findtext("description") or "")
        articles.append(
            {
                **descriptors[path],
                "title": item.findtext("title"),
                "url": url,
                "summary": "".join(plain.parts),
                "category": path.strip("/").split("/")[0],
            }
        )
    if not articles or len(articles) > 19:
        raise SystemExit("Expected 1–19 articles; review the choice budget before updating")
    (ROOT / "data/articles.json").write_text(
        json.dumps(
            {
                "source": SOURCE,
                "fetched_at": datetime.now(UTC).isoformat(),
                "articles": articles,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(articles)} articles")


if __name__ == "__main__":
    main()

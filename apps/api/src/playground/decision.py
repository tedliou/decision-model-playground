from dataclasses import dataclass

from playground.schemas import Catalog

PROMPT_VERSION = "article-choice-v2"
INSTRUCTIONS = "Which article best answers the reader's question? Choose none if no article helps."


@dataclass(frozen=True)
class Decision:
    state: str
    criteria: dict[str, str]

    @property
    def questions(self) -> dict:
        return {
            "recommendation": {
                "type": "choice",
                "instructions": INSTRUCTIONS,
                "criteria": self.criteria,
            }
        }


def build_decision(question: str, catalog: Catalog) -> Decision:
    return Decision(
        state=question,
        criteria={
            **{a.id: a.decision_label for a in catalog.articles},
            "none": "No relevant article",
        },
    )

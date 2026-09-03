from dataclasses import dataclass, field
import re

from temperans.anchors import AnchorExtractor


@dataclass
class ExtractedWorkState:
    goal: str
    current_problem: str
    entities: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    anchors: list = field(default_factory=list)


class WorkStateExtractor:
    """
    Conservative V1 extractor.

    Extraction depends only on the incoming event. Existing trajectory
    candidates are intentionally not accepted as input, structurally
    preventing candidate-goal circularity.
    """

    def __init__(self, anchor_extractor=None):
        self.anchor_extractor = anchor_extractor or AnchorExtractor()

    def extract(
        self,
        *,
        text,
        supplied_goal="",
        entities=None,
        artifacts=None,
    ):
        text = " ".join((text or "").strip().split())
        goal = " ".join((supplied_goal or "").strip().split())

        if not goal:
            words = re.findall(r"[A-Za-z0-9_#.-]+", text)
            goal = " ".join(words[:12])

        return ExtractedWorkState(
            goal=goal,
            current_problem=text,
            entities=list(entities or []),
            artifacts=list(artifacts or []),
            anchors=list(self.anchor_extractor.extract(text) or []),
        )

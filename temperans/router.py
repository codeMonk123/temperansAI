from dataclasses import dataclass, asdict
from enum import Enum
import re
import uuid

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RoutingDecision(str, Enum):
    ATTACH = "attach"
    SUGGEST = "suggest"
    NEW = "new"


@dataclass
class GoalState:
    summary: str
    entities: list
    intent: str

    def to_dict(self):
        return asdict(self)


@dataclass
class RoutingResult:
    decision: RoutingDecision
    thread_id: str
    score: float
    margin: float
    second_score: float
    is_new: bool
    goal_state: GoalState
    evidence: list

    def to_dict(self):
        result = asdict(self)
        result["decision"] = self.decision.value
        return result


class GoalStateExtractor:
    """
    Deterministic V0 extractor.

    This establishes the GoalState contract.
    A learned/LLM extractor can replace the internals later.
    """

    INTENT_WORDS = {
        "debug": {
            "fail", "fails", "failing", "failed",
            "error", "crash", "crashes", "broken",
            "debug", "fix", "issue", "problem",
        },
        "research": {
            "compare", "research", "program",
            "programs", "school", "schools",
            "master", "masters", "university",
        },
        "evaluate": {
            "benchmark", "evaluate", "evaluation",
            "test", "testing", "score", "metric",
            "history", "trajectory",
        },
    }

    def extract(self, text):
        clean = " ".join(text.strip().split())
        tokens = re.findall(
            r"[A-Za-z0-9_.-]+",
            clean.lower(),
        )

        token_set = set(tokens)

        intent = "general"
        best_overlap = 0

        for candidate, words in self.INTENT_WORDS.items():
            overlap = len(token_set & words)

            if overlap > best_overlap:
                best_overlap = overlap
                intent = candidate

        # V0 entity candidates:
        # preserve technical/specific terms while removing
        # very common conversational words.
        stop = {
            "the", "a", "an", "and", "or", "but",
            "is", "are", "was", "were", "be",
            "to", "of", "in", "on", "for", "with",
            "my", "i", "we", "you", "it", "this",
            "that", "what", "how", "should",
            "now", "still", "does", "do",
        }

        entities = []

        for token in tokens:
            if (
                len(token) >= 5
                and token not in stop
                and token not in entities
            ):
                entities.append(token)

        return GoalState(
            summary=clean,
            entities=entities[:12],
            intent=intent,
        )


class TrajectoryRouter:
    """
    High-precision trajectory router.

    Policy:
      high score + clear margin -> ATTACH
      plausible but ambiguous   -> SUGGEST
      otherwise                 -> NEW

    False merges are intentionally treated as
    more expensive than false splits.
    """

    def __init__(
        self,
        attach_threshold=0.30,
        suggest_threshold=0.15,
        margin_threshold=0.08,
        extractor=None,
    ):
        self.attach_threshold = attach_threshold
        self.suggest_threshold = suggest_threshold
        self.margin_threshold = margin_threshold
        self.extractor = (
            extractor or GoalStateExtractor()
        )

    def _new_thread_id(self):
        return "thread_" + uuid.uuid4().hex[:12]

    def _thread_documents(self, events):
        docs = {}

        for event in events:
            if not event.thread_id:
                continue

            text = (event.text or "").strip()

            if not text:
                continue

            docs.setdefault(
                event.thread_id,
                [],
            ).append(text)

        return {
            thread_id: " ".join(texts)
            for thread_id, texts in docs.items()
        }

    def resolve(
        self,
        text,
        events,
    ):
        goal = self.extractor.extract(text)

        query_text = (
            goal.routing_text()
            if hasattr(goal, "routing_text")
            else goal.summary
        )

        documents = self._thread_documents(events)

        if not documents:
            thread_id = self._new_thread_id()

            return RoutingResult(
                decision=RoutingDecision.NEW,
                thread_id=thread_id,
                score=1.0,
                margin=1.0,
                second_score=0.0,
                is_new=True,
                goal_state=goal,
                evidence=[
                    "no existing trajectories"
                ],
            )

        thread_ids = list(documents.keys())

        candidate_texts = []

        for thread_id in thread_ids:
            candidate_goal = self.extractor.extract(
                documents[thread_id]
            )

            candidate_text = (
                candidate_goal.routing_text()
                if hasattr(
                    candidate_goal,
                    "routing_text",
                )
                else candidate_goal.summary
            )

            candidate_texts.append(
                candidate_text
            )

        corpus = [
            query_text,
            *candidate_texts,
        ]

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
        )

        matrix = vectorizer.fit_transform(corpus)

        similarities = cosine_similarity(
            matrix[0:1],
            matrix[1:],
        )[0]

        ranked = sorted(
            zip(thread_ids, similarities),
            key=lambda item: item[1],
            reverse=True,
        )

        best_thread, best_score = ranked[0]

        second_score = (
            float(ranked[1][1])
            if len(ranked) > 1
            else 0.0
        )

        best_score = float(best_score)
        margin = best_score - second_score

        evidence = [
            f"best trajectory similarity={best_score:.3f}",
            f"second-best similarity={second_score:.3f}",
            f"routing margin={margin:.3f}",
            f"intent={goal.intent}",
        ]

        if (
            best_score >= self.attach_threshold
            and margin >= self.margin_threshold
        ):
            decision = RoutingDecision.ATTACH
            thread_id = best_thread
            is_new = False

            evidence.append(
                "high-confidence existing trajectory"
            )

        elif best_score >= self.suggest_threshold:
            decision = RoutingDecision.SUGGEST
            thread_id = best_thread
            is_new = False

            evidence.append(
                "plausible but ambiguous trajectory"
            )

        else:
            decision = RoutingDecision.NEW
            thread_id = self._new_thread_id()
            is_new = True

            evidence.append(
                "insufficient evidence for safe merge"
            )

        return RoutingResult(
            decision=decision,
            thread_id=thread_id,
            score=round(best_score, 4),
            margin=round(margin, 4),
            second_score=round(
                second_score,
                4,
            ),
            is_new=is_new,
            goal_state=goal,
            evidence=evidence,
        )

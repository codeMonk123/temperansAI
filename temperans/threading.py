from dataclasses import dataclass
from uuid import uuid4

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ThreadResult:
    thread_id: str
    confidence: float
    is_new: bool
    method: str

    def to_dict(self):
        return {
            "thread_id": self.thread_id,
            "confidence": self.confidence,
            "is_new": self.is_new,
            "method": self.method,
        }


class ThreadResolver:
    def resolve(
        self,
        text: str,
        existing_threads: dict,
    ) -> ThreadResult:
        raise NotImplementedError


class SemanticThreadResolver:
    """
    Alpha thread resolver.

    existing_threads format:

    {
        "thread_id": [
            "previous human text",
            "another human text",
        ]
    }
    """

    def __init__(
        self,
        threshold=0.15,
    ):
        self.threshold = threshold

    def _new_thread(self):
        return ThreadResult(
            thread_id="thread_" + uuid4().hex[:12],
            confidence=1.0,
            is_new=True,
            method="tfidf-v0",
        )

    def resolve(
        self,
        text: str,
        existing_threads: dict,
    ) -> ThreadResult:

        if not existing_threads:
            return self._new_thread()

        thread_ids = []
        documents = []

        for thread_id, texts in existing_threads.items():

            if not texts:
                continue

            thread_ids.append(thread_id)

            # Represent a thread using its recent
            # human-event history.
            documents.append(
                " ".join(texts[-10:])
            )

        if not documents:
            return self._new_thread()

        corpus = documents + [text]

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
        )

        X = vectorizer.fit_transform(corpus)

        incoming = X[-1]

        scores = cosine_similarity(
            incoming,
            X[:-1],
        )[0]

        best_index = int(scores.argmax())
        best_score = float(scores[best_index])

        if best_score < self.threshold:
            return self._new_thread()

        return ThreadResult(
            thread_id=thread_ids[best_index],
            confidence=best_score,
            is_new=False,
            method="tfidf-v0",
        )

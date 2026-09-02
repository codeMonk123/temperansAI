from dataclasses import dataclass
from collections import Counter, defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from temperans.ttlb import (
    ATTACH,
    BRANCH,
    NEW,
    build_v0_cases,
)


@dataclass
class Prediction:
    case_id: str
    expected: str
    predicted: str
    score: float
    correct: bool
    category: str
    difficulty: str


class TfidfLinkageBaseline:
    """
    Deliberately simple lexical baseline.

    It cannot reliably identify BRANCH.
    That's useful: future trajectory intelligence
    should materially outperform this baseline.
    """

    def __init__(
        self,
        attach_threshold=0.15,
    ):
        self.attach_threshold = attach_threshold

    def predict(self, case):
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
        )

        matrix = vectorizer.fit_transform([
            case.candidate_text,
            case.new_text,
        ])

        score = float(
            cosine_similarity(
                matrix[0:1],
                matrix[1:2],
            )[0][0]
        )

        predicted = (
            ATTACH
            if score >= self.attach_threshold
            else NEW
        )

        return predicted, score


def evaluate(
    model,
    cases=None,
):
    cases = cases or build_v0_cases()

    predictions = []

    for case in cases:
        predicted, score = model.predict(case)

        predictions.append(
            Prediction(
                case_id=case.case_id,
                expected=case.label,
                predicted=predicted,
                score=score,
                correct=(predicted == case.label),
                category=case.category,
                difficulty=case.difficulty,
            )
        )

    return predictions


def metrics(predictions):
    total = len(predictions)

    correct = sum(
        prediction.correct
        for prediction in predictions
    )

    confusion = Counter(
        (
            prediction.expected,
            prediction.predicted,
        )
        for prediction in predictions
    )

    by_category = defaultdict(
        lambda: [0, 0]
    )

    for prediction in predictions:
        bucket = by_category[
            prediction.category
        ]

        bucket[1] += 1

        if prediction.correct:
            bucket[0] += 1

    category_accuracy = {
        category: round(
            correct_count / count,
            4,
        )
        for category, (
            correct_count,
            count,
        ) in by_category.items()
    }

    # False merge:
    # Ground truth says NEW/BRANCH,
    # baseline incorrectly ATTACHes.
    false_merges = sum(
        1
        for prediction in predictions
        if (
            prediction.expected
            in {NEW, BRANCH}
            and prediction.predicted == ATTACH
        )
    )

    # False split:
    # Ground truth says ATTACH,
    # baseline creates NEW.
    false_splits = sum(
        1
        for prediction in predictions
        if (
            prediction.expected == ATTACH
            and prediction.predicted == NEW
        )
    )

    return {
        "cases": total,
        "correct": correct,
        "accuracy": round(
            correct / total,
            4,
        ) if total else 0.0,
        "false_merges": false_merges,
        "false_splits": false_splits,
        "confusion": dict(confusion),
        "category_accuracy": category_accuracy,
    }


def print_report(
    predictions,
):
    result = metrics(predictions)

    print("=" * 72)
    print("TTLB EVALUATION")
    print("=" * 72)

    for prediction in predictions:
        mark = (
            "PASS"
            if prediction.correct
            else "FAIL"
        )

        print(
            f"{mark:4} "
            f"{prediction.case_id:24} "
            f"expected={prediction.expected:6} "
            f"predicted={prediction.predicted:6} "
            f"score={prediction.score:.4f}"
        )

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print("CASES:", result["cases"])
    print("CORRECT:", result["correct"])
    print("ACCURACY:", result["accuracy"])
    print(
        "FALSE MERGES:",
        result["false_merges"],
    )
    print(
        "FALSE SPLITS:",
        result["false_splits"],
    )

    print()
    print("CATEGORY ACCURACY")

    for category, accuracy in (
        result["category_accuracy"].items()
    ):
        print(
            f"{category:32} {accuracy:.3f}"
        )

    return result


if __name__ == "__main__":
    predictions = evaluate(
        TfidfLinkageBaseline()
    )

    print_report(predictions)

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from temperans.ttlb import (
    ATTACH,
    NEW,
    build_v0_cases,
)

from temperans.ttlb_eval import (
    Prediction,
    print_report,
)


class SemanticLinkageBaseline:
    """
    Local semantic similarity baseline.

    IMPORTANT:
    This is still similarity, not trajectory reasoning.

    It establishes how far generic embeddings can get
    before anchors, contradictions, trajectory state,
    or frontier reasoning are added.
    """

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        attach_threshold=0.55,
    ):
        self.model = SentenceTransformer(
            model_name
        )

        self.attach_threshold = (
            attach_threshold
        )

    def predict(self, case):
        embeddings = self.model.encode(
            [
                case.candidate_text,
                case.new_text,
            ],
            normalize_embeddings=True,
        )

        score = float(
            cosine_similarity(
                embeddings[0:1],
                embeddings[1:2],
            )[0][0]
        )

        # Generic similarity cannot reliably
        # distinguish BRANCH yet.
        predicted = (
            ATTACH
            if score >= self.attach_threshold
            else NEW
        )

        return predicted, score


def evaluate_semantic(
    model,
    cases=None,
):
    cases = cases or build_v0_cases()

    predictions = []

    for case in cases:
        predicted, score = model.predict(
            case
        )

        predictions.append(
            Prediction(
                case_id=case.case_id,
                expected=case.label,
                predicted=predicted,
                score=score,
                correct=(
                    predicted == case.label
                ),
                category=case.category,
                difficulty=case.difficulty,
            )
        )

    return predictions


if __name__ == "__main__":
    model = SemanticLinkageBaseline()

    predictions = evaluate_semantic(
        model
    )

    print_report(predictions)

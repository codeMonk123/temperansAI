import json
import random
import numpy as np
import torch

from transformers import AutoTokenizer, AutoModelForCausalLM
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
)

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

TRAIN_PATH = (
    "data/annotation/temperans_v0_train_clean.jsonl"
)

TEST_PATH = (
    "data/annotation/temperans_bench_v0_eval3class19.jsonl"
)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

LABELS = ["continue", "new_topic", "repair"]


def load_jsonl(path):
    with open(path) as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


train = load_jsonl(TRAIN_PATH)
test = load_jsonl(TEST_PATH)

print("TRAIN:", len(train))
print("TEST:", len(test))


# --------------------------------------------------
# Verify zero trajectory leakage
# --------------------------------------------------

train_ids = {
    x["trajectory_id"]
    for x in train
}

test_ids = {
    x["trajectory_id"]
    for x in test
}

assert train_ids.isdisjoint(test_ids)

print("Trajectory leakage: 0")


# --------------------------------------------------
# Normalize training rows
# --------------------------------------------------

train_rows = []

for x in train:

    events = x["events"]

    current = events[-1]

    if len(events) >= 2:
        previous = events[-2]
        previous_text = previous["text"]
    else:
        previous_text = ""

    train_rows.append({
        "trajectory_id": x["trajectory_id"],
        "current": current["text"],
        "previous": previous_text,
        "label": x["primitive"],
    })


test_rows = []

for x in test:

    test_rows.append({
        "trajectory_id": x["trajectory_id"],
        "current": x["target_text"],
        "previous": x["previous_text"],
        "label": x["human_label"],
    })


# --------------------------------------------------
# Construct deterministic shuffled histories
# --------------------------------------------------

train_histories = [
    x["previous"]
    for x in train_rows
]

test_histories = [
    x["previous"]
    for x in test_rows
]

rng = random.Random(SEED)

train_perm = list(range(len(train_rows)))
test_perm = list(range(len(test_rows)))

rng.shuffle(train_perm)
rng.shuffle(test_perm)


# Prevent self-history where possible.

def fix_self_permutation(perm):

    n = len(perm)

    for i in range(n):

        if perm[i] == i:
            j = (i + 1) % n
            perm[i], perm[j] = perm[j], perm[i]

    return perm


train_perm = fix_self_permutation(train_perm)
test_perm = fix_self_permutation(test_perm)

for i, j in enumerate(test_perm):
    assert i != j


for i, x in enumerate(train_rows):
    x["wrong_previous"] = train_histories[
        train_perm[i]
    ]


for i, x in enumerate(test_rows):
    x["wrong_previous"] = test_histories[
        test_perm[i]
    ]


# --------------------------------------------------
# Load Qwen
# --------------------------------------------------

print("\nLoading Qwen...")

tokenizer = AutoTokenizer.from_pretrained(MODEL)

model = AutoModelForCausalLM.from_pretrained(MODEL)

model.eval()

DEVICE = torch.device(
    "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

model.to(DEVICE)

print("DEVICE:", DEVICE)
print("HIDDEN SIZE:", model.config.hidden_size)


# --------------------------------------------------
# Representation functions
# --------------------------------------------------

@torch.no_grad()
def embed_current(text):

    formatted = "HUMAN: " + text

    inputs = tokenizer(
        formatted,
        return_tensors="pt",
        truncation=True,
        max_length=256,
    ).to(DEVICE)

    outputs = model(
        **inputs,
        output_hidden_states=True,
        use_cache=False,
    )

    hidden = outputs.hidden_states[-1][0]

    return (
        hidden.mean(dim=0)
        .cpu()
        .numpy()
        .astype("float32")
    )


@torch.no_grad()
def embed_conditioned(previous, current):

    prefix = (
        "PREVIOUS:\n"
        + previous
        + "\n\nCURRENT:\n"
    )

    current_text = current

    # Tokenize separately so we know exactly where
    # CURRENT tokens begin.

    prefix_ids = tokenizer(
        prefix,
        add_special_tokens=False,
    )["input_ids"]

    current_ids = tokenizer(
        current_text,
        add_special_tokens=False,
    )["input_ids"]

    # Reserve up to 256 tokens for current.
    current_ids = current_ids[-256:]

    # Total sequence capped at 768.
    max_total = 768

    history_budget = max_total - len(current_ids)

    if history_budget < 1:
        history_budget = 1

    prefix_ids = prefix_ids[-history_budget:]

    ids = prefix_ids + current_ids

    input_ids = torch.tensor(
        [ids],
        dtype=torch.long,
        device=DEVICE,
    )

    attention_mask = torch.ones_like(input_ids)

    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        output_hidden_states=True,
        use_cache=False,
    )

    hidden = outputs.hidden_states[-1][0]

    current_start = len(prefix_ids)

    current_hidden = hidden[current_start:]

    assert current_hidden.shape[0] > 0

    return (
        current_hidden.mean(dim=0)
        .cpu()
        .numpy()
        .astype("float32")
    )


def build_embeddings(rows, condition):

    X = []

    for i, x in enumerate(rows, 1):

        if condition == "current":

            vec = embed_current(
                x["current"]
            )

        elif condition == "correct":

            vec = embed_conditioned(
                x["previous"],
                x["current"],
            )

        elif condition == "shuffled":

            vec = embed_conditioned(
                x["wrong_previous"],
                x["current"],
            )

        else:
            raise ValueError(condition)

        X.append(vec)

        if i % 10 == 0 or i == len(rows):
            print(
                f"{condition}: "
                f"{i}/{len(rows)}"
            )

    return np.stack(X)


# --------------------------------------------------
# Evaluation helper
# --------------------------------------------------

def evaluate_condition(
    name,
    X_train,
    X_test,
    y_train,
    y_test,
):

    clf = LogisticRegression(
        max_iter=5000,
        class_weight="balanced",
        random_state=SEED,
    )

    clf.fit(
        X_train,
        y_train,
    )

    pred = clf.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        pred,
    )

    macro_f1 = f1_score(
        y_test,
        pred,
        labels=LABELS,
        average="macro",
        zero_division=0,
    )

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print(
        "Accuracy:",
        round(accuracy, 3)
    )

    print(
        "Macro-F1:",
        round(macro_f1, 3)
    )

    print()

    print(
        classification_report(
            y_test,
            pred,
            labels=LABELS,
            zero_division=0,
        )
    )

    return {
        "name": name,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "predictions": pred.tolist(),
    }


y_train = np.array([
    x["label"]
    for x in train_rows
])

y_test = np.array([
    x["label"]
    for x in test_rows
])


# --------------------------------------------------
# 1. TF-IDF current-only baseline
# --------------------------------------------------

print("\nBuilding TF-IDF baseline...")

tfidf = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1,
    max_features=10000,
)

X_train_tf = tfidf.fit_transform(
    [x["current"] for x in train_rows]
)

X_test_tf = tfidf.transform(
    [x["current"] for x in test_rows]
)

tfidf_clf = LogisticRegression(
    max_iter=5000,
    class_weight="balanced",
    random_state=SEED,
)

tfidf_clf.fit(
    X_train_tf,
    y_train,
)

tfidf_pred = tfidf_clf.predict(
    X_test_tf
)

tfidf_accuracy = accuracy_score(
    y_test,
    tfidf_pred,
)

tfidf_f1 = f1_score(
    y_test,
    tfidf_pred,
    labels=LABELS,
    average="macro",
    zero_division=0,
)

print("\n" + "=" * 70)
print("TF-IDF CURRENT ONLY")
print("=" * 70)

print(
    "Accuracy:",
    round(tfidf_accuracy, 3)
)

print(
    "Macro-F1:",
    round(tfidf_f1, 3)
)


# --------------------------------------------------
# 2. Qwen current-only
# --------------------------------------------------

print("\nEmbedding CURRENT condition...")

X_train_current = build_embeddings(
    train_rows,
    "current",
)

X_test_current = build_embeddings(
    test_rows,
    "current",
)

current_result = evaluate_condition(
    "QWEN CURRENT ONLY",
    X_train_current,
    X_test_current,
    y_train,
    y_test,
)


# --------------------------------------------------
# 3. Correct trajectory
# --------------------------------------------------

print("\nEmbedding CORRECT trajectory...")

X_train_correct = build_embeddings(
    train_rows,
    "correct",
)

X_test_correct = build_embeddings(
    test_rows,
    "correct",
)

correct_result = evaluate_condition(
    "QWEN CORRECT TRAJECTORY",
    X_train_correct,
    X_test_correct,
    y_train,
    y_test,
)


# --------------------------------------------------
# 4. Shuffled trajectory
# --------------------------------------------------

print("\nEmbedding SHUFFLED trajectory...")

X_train_shuffled = build_embeddings(
    train_rows,
    "shuffled",
)

X_test_shuffled = build_embeddings(
    test_rows,
    "shuffled",
)

shuffled_result = evaluate_condition(
    "QWEN SHUFFLED TRAJECTORY",
    X_train_shuffled,
    X_test_shuffled,
    y_train,
    y_test,
)


# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\n")
print("=" * 70)
print("TEMPERANS-BENCH V0 SUMMARY")
print("=" * 70)

print(
    f"{'Condition':30s} "
    f"{'Accuracy':>10s} "
    f"{'Macro-F1':>10s}"
)

print("-" * 54)

print(
    f"{'TF-IDF current':30s} "
    f"{tfidf_accuracy:10.3f} "
    f"{tfidf_f1:10.3f}"
)

for r in [
    current_result,
    correct_result,
    shuffled_result,
]:

    print(
        f"{r['name']:30s} "
        f"{r['accuracy']:10.3f} "
        f"{r['macro_f1']:10.3f}"
    )


print()
print(
    "Correct - Current Macro-F1:",
    round(
        correct_result["macro_f1"]
        - current_result["macro_f1"],
        3,
    )
)

print(
    "Correct - Shuffled Macro-F1:",
    round(
        correct_result["macro_f1"]
        - shuffled_result["macro_f1"],
        3,
    )
)


# --------------------------------------------------
# Save results
# --------------------------------------------------

results = {
    "benchmark": "temperans_bench_v0_eval3class19",
    "train_examples": len(train_rows),
    "test_examples": len(test_rows),
    "seed": SEED,

    "tfidf_current": {
        "accuracy": tfidf_accuracy,
        "macro_f1": tfidf_f1,
        "predictions": tfidf_pred.tolist(),
    },

    "qwen_current": current_result,
    "qwen_correct_trajectory": correct_result,
    "qwen_shuffled_trajectory": shuffled_result,
}

with open(
    "temperans_bench_v0_results.json",
    "w",
) as f:

    json.dump(
        results,
        f,
        indent=2,
    )


print(
    "\nSaved: "
    "temperans_bench_v0_results.json"
)

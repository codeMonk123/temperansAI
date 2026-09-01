import json
import pickle
import random
import numpy as np
import torch
import torch.nn as nn

from transformers import AutoTokenizer, AutoModelForCausalLM
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

TRAIN_PATH = "data/annotation/temperans_v1_train3class.jsonl"
TEST_PATH = "data/annotation/temperans_bench_v0_eval3class19.jsonl"

SEED = 42
LABELS = ["continue", "new_topic", "repair"]

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


def load(path):
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


train = load(TRAIN_PATH)
test = load(TEST_PATH)

train_ids = {x["trajectory_id"] for x in train}
test_ids = {x["trajectory_id"] for x in test}

assert train_ids.isdisjoint(test_ids)

print("TRAIN:", len(train))
print("TEST:", len(test))
print("TRAJECTORY LEAKAGE: 0")


# --------------------------------------------------
# Normalize
# --------------------------------------------------

train_rows = [
    {
        "trajectory_id": x["trajectory_id"],
        "previous": x["previous_text"],
        "current": x["target_text"],
        "label": x["history_aware"],
    }
    for x in train
]

test_rows = [
    {
        "trajectory_id": x["trajectory_id"],
        "previous": x["previous_text"],
        "current": x["target_text"],
        "label": x["human_label"],
    }
    for x in test
]


# --------------------------------------------------
# Wrong histories
# --------------------------------------------------

def derangement(n, seed):
    rng = random.Random(seed)

    while True:
        p = list(range(n))
        rng.shuffle(p)

        if all(i != p[i] for i in range(n)):
            return p


train_perm = derangement(len(train_rows), SEED)
test_perm = derangement(len(test_rows), SEED)

for i, row in enumerate(train_rows):
    row["wrong_previous"] = train_rows[
        train_perm[i]
    ]["previous"]

for i, row in enumerate(test_rows):
    row["wrong_previous"] = test_rows[
        test_perm[i]
    ]["previous"]


# --------------------------------------------------
# Qwen
# --------------------------------------------------

print("\nLoading Qwen...")

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL)
model.eval()

device = torch.device(
    "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

model.to(device)

H = model.config.hidden_size

print("DEVICE:", device)
print("HIDDEN:", H)


# --------------------------------------------------
# Embeddings
#
# Return:
# current representation conditioned on history
# history representation
# relational feature
# --------------------------------------------------

@torch.no_grad()
def pair_embedding(previous, current):

    prev_ids = tokenizer(
        "PREVIOUS:\n" + previous + "\n\nCURRENT:\n",
        add_special_tokens=False,
    )["input_ids"]

    cur_ids = tokenizer(
        current,
        add_special_tokens=False,
    )["input_ids"]

    cur_ids = cur_ids[-256:]

    budget = max(1, 768 - len(cur_ids))
    prev_ids = prev_ids[-budget:]

    ids = prev_ids + cur_ids

    input_ids = torch.tensor(
        [ids],
        dtype=torch.long,
        device=device,
    )

    mask = torch.ones_like(input_ids)

    out = model(
        input_ids=input_ids,
        attention_mask=mask,
        output_hidden_states=True,
        use_cache=False,
    )

    hidden = out.hidden_states[-1][0]

    split = len(prev_ids)

    h_history = hidden[:split].mean(dim=0)
    h_current = hidden[split:].mean(dim=0)

    # Explicit relational representation.
    feature = torch.cat([
        h_current,
        h_history,
        h_current - h_history,
        h_current * h_history,
    ])

    return feature.cpu().numpy().astype("float32")


def embed_rows(rows, history_key, name):

    X = []

    for i, row in enumerate(rows, 1):

        X.append(
            pair_embedding(
                row[history_key],
                row["current"],
            )
        )

        if i % 10 == 0 or i == len(rows):
            print(f"{name}: {i}/{len(rows)}")

    return np.stack(X)


# --------------------------------------------------
# Cache representations
# --------------------------------------------------

print("\nTRAIN correct histories")
X_train_correct = embed_rows(
    train_rows,
    "previous",
    "train-correct",
)

print("\nTRAIN wrong histories")
X_train_wrong = embed_rows(
    train_rows,
    "wrong_previous",
    "train-wrong",
)

print("\nTEST correct histories")
X_test_correct = embed_rows(
    test_rows,
    "previous",
    "test-correct",
)

print("\nTEST wrong histories")
X_test_wrong = embed_rows(
    test_rows,
    "wrong_previous",
    "test-wrong",
)

y_train = np.array([x["label"] for x in train_rows])
y_test = np.array([x["label"] for x in test_rows])


# --------------------------------------------------
# Primitive head
#
# Train primitive prediction ONLY on correct history.
# --------------------------------------------------

primitive = LogisticRegression(
    max_iter=5000,
    class_weight="balanced",
    random_state=SEED,
)

primitive.fit(
    X_train_correct,
    y_train,
)


def primitive_eval(name, X):

    pred = primitive.predict(X)

    acc = accuracy_score(y_test, pred)

    f1 = f1_score(
        y_test,
        pred,
        labels=LABELS,
        average="macro",
        zero_division=0,
    )

    print(
        f"{name:28s} "
        f"accuracy={acc:.3f} "
        f"macro_f1={f1:.3f}"
    )

    return acc, f1, pred


# --------------------------------------------------
# History-match auxiliary head
# --------------------------------------------------

X_match_train = np.concatenate([
    X_train_correct,
    X_train_wrong,
])

y_match_train = np.concatenate([
    np.ones(len(X_train_correct)),
    np.zeros(len(X_train_wrong)),
])

match_head = LogisticRegression(
    max_iter=5000,
    class_weight="balanced",
    random_state=SEED,
)

match_head.fit(
    X_match_train,
    y_match_train,
)

with open("temperans_v1_primitive_head.pkl", "wb") as f:
    pickle.dump(primitive, f)

with open("temperans_v1_match_head.pkl", "wb") as f:
    pickle.dump(match_head, f)

print("Saved V1 model heads")

X_match_test = np.concatenate([
    X_test_correct,
    X_test_wrong,
])

y_match_test = np.concatenate([
    np.ones(len(X_test_correct)),
    np.zeros(len(X_test_wrong)),
])

match_pred = match_head.predict(X_match_test)

match_acc = accuracy_score(
    y_match_test,
    match_pred,
)


# --------------------------------------------------
# Results
# --------------------------------------------------

print("\n" + "=" * 70)
print("TEMPERANS V1 — FROZEN GOLD19")
print("=" * 70)

correct_acc, correct_f1, correct_pred = primitive_eval(
    "CORRECT HISTORY",
    X_test_correct,
)

wrong_acc, wrong_f1, wrong_pred = primitive_eval(
    "SHUFFLED HISTORY",
    X_test_wrong,
)

print()
print(
    "Correct - Shuffled Macro-F1:",
    round(correct_f1 - wrong_f1, 3)
)

print(
    "History-match accuracy:",
    round(match_acc, 3)
)


# --------------------------------------------------
# Save
# --------------------------------------------------

results = {
    "experiment": "temperans_v1",
    "train_examples": len(train_rows),
    "test_examples": len(test_rows),
    "train_gold_overlap": 0,
    "seed": SEED,

    "correct_history": {
        "accuracy": correct_acc,
        "macro_f1": correct_f1,
        "predictions": correct_pred.tolist(),
    },

    "shuffled_history": {
        "accuracy": wrong_acc,
        "macro_f1": wrong_f1,
        "predictions": wrong_pred.tolist(),
    },

    "correct_minus_shuffled_macro_f1":
        correct_f1 - wrong_f1,

    "history_match_accuracy": match_acc,
}

with open(
    "temperans_v1_results.json",
    "w",
) as f:
    json.dump(results, f, indent=2)

np.save(
    "data/annotation/temperans_v1_train_correct_X.npy",
    X_train_correct,
)

np.save(
    "data/annotation/temperans_v1_train_wrong_X.npy",
    X_train_wrong,
)

print("\nSaved temperans_v1_results.json")

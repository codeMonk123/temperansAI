import json
import random
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

random.seed(42)

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
SRC = "data/annotation/short_ambiguous_turns.jsonl"

with open(SRC) as f:
    rows = [json.loads(x) for x in f]

rows = random.sample(rows, min(400, len(rows)))

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL)
model.eval()

vectors = []

with torch.no_grad():

    for i, x in enumerate(rows, 1):

        inputs = tokenizer(
            x["target_text"],
            return_tensors="pt",
            truncation=True,
            max_length=128
        )

        outputs = model(
            **inputs,
            output_hidden_states=True,
            use_cache=False
        )

        vec = (
            outputs.hidden_states[-1][0]
            .mean(dim=0)
            .cpu()
            .numpy()
        )

        vectors.append(vec)

        if i % 50 == 0:
            print(f"embedded {i}/{len(rows)}")

V = np.stack(vectors)
V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-8

S = V @ V.T

pairs = []

for i in range(len(rows)):
    for j in range(i + 1, len(rows)):

        if rows[i]["trajectory_id"] == rows[j]["trajectory_id"]:
            continue

        sim = float(S[i,j])

        if sim >= 0.88:
            pairs.append((sim, i, j))

pairs.sort(reverse=True)

print("\nhigh-similarity pairs:", len(pairs))

print("\nTOP 20:")

shown = 0

for sim, i, j in pairs:

    a = " ".join(rows[i]["target_text"].split())
    b = " ".join(rows[j]["target_text"].split())

    # Ignore exact duplicate strings for this inspection.
    if a.lower() == b.lower():
        continue

    print("\n" + "-" * 70)
    print("SIM:", round(sim, 3))
    print("A:", a[:180])
    print("B:", b[:180])

    shown += 1

    if shown == 20:
        break

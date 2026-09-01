import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
SRC = "data/normalized/wildchat_events_v1.jsonl"
OUT_VEC = "data/annotation/transition_embeddings_500.npy"
OUT_META = "data/annotation/transition_embeddings_500.jsonl"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL)
model.eval()

trajectories = {}

with open(SRC) as f:
    for line in f:
        e = json.loads(line)
        if e.get("language") == "English":
            trajectories.setdefault(
                e["trajectory_id"], []
            ).append(e)

candidates = []

for tid, events in trajectories.items():
    events.sort(key=lambda x: x["event_index"])

    for i in range(1, len(events)):
        current = events[i]

        if current["source"]["type"] != "human":
            continue

        previous = events[i - 1]

        candidates.append({
            "trajectory_id": tid,
            "target_event_index": current["event_index"],
            "previous_text": previous["text"],
            "target_text": current["text"]
        })

candidates = candidates[:500]
vectors = []

with torch.no_grad():

    for i, x in enumerate(candidates, 1):

        text = (
            "Previous response:\n"
            + x["previous_text"][-1000:]
            + "\n\nCurrent user response:\n"
            + x["target_text"][:1500]
        )

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        outputs = model(
            **inputs,
            output_hidden_states=True,
            use_cache=False
        )

        hidden = outputs.hidden_states[-1][0]

        vec = hidden.mean(dim=0)
        vectors.append(vec.cpu().numpy())

        if i % 50 == 0:
            print(f"embedded {i}/500")

matrix = np.stack(vectors).astype("float32")

np.save(OUT_VEC, matrix)

with open(OUT_META, "w") as f:
    for x in candidates:
        f.write(
            json.dumps(x, ensure_ascii=False) + "\n"
        )

print("vectors:", len(vectors))
print("shape:", matrix.shape)
print("saved:", OUT_VEC)

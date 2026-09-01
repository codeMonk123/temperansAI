import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
SRC = "data/annotation/benchmark3_expanded_trajectory_examples.jsonl"

OUT_X = "data/annotation/benchmark3_trajectory_X.npy"
OUT_Y = "data/annotation/benchmark3_trajectory_y.npy"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL)
model.eval()

with open(SRC) as f:
    rows = [json.loads(x) for x in f]

def embed(text, max_length):
    if not text.strip():
        return torch.zeros(model.config.hidden_size)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length
    )

    outputs = model(
        **inputs,
        output_hidden_states=True,
        use_cache=False
    )

    hidden = outputs.hidden_states[-1][0]

    return hidden.mean(dim=0)

X = []
Y = []

with torch.no_grad():

    for i, row in enumerate(rows, 1):

        events = row["events"]
        current = events[-1]
        history = events[:-1]

        current_text = (
            f"{current['source_type'].upper()}: "
            f"{current['text']}"
        )

        history_text = "\n".join(
            f"{e['source_type'].upper()}: {e['text']}"
            for e in history
        )

        h_current = embed(
            current_text[:3000],
            max_length=256
        )

        h_history = embed(
            history_text[-6000:],
            max_length=512
        )

        feature = torch.cat([
            h_current,
            h_history,
            h_current - h_history,
            h_current * h_history
        ])

        X.append(feature.cpu().numpy())
        Y.append(row["primitive"])

        if i % 10 == 0:
            print(f"processed {i}/{len(rows)}")

X = np.stack(X).astype("float32")
Y = np.array(Y)

np.save(OUT_X, X)
np.save(OUT_Y, Y)

print("shape:", X.shape)
print("labels:", len(Y))

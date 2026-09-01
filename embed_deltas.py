import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
SRC = "data/annotation/transition_embeddings_all.jsonl"
OUT = "data/annotation/transition_deltas_500.npy"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL)
model.eval()

with open(SRC) as f:
    rows = [json.loads(x) for x in f][:500]

def embed(text):
    if not isinstance(text, str) or not text.strip():
        return None

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256
    )

    outputs = model(
        **inputs,
        output_hidden_states=True,
        use_cache=False
    )

    return outputs.hidden_states[-1][0].mean(dim=0)

deltas = []

with torch.no_grad():
    for i, x in enumerate(rows, 1):

        prev = embed(x["previous_text"][-1000:])
        curr = embed(x["target_text"][:1500])

        if prev is None or curr is None:
            print(f"skip {i}: empty text")
            deltas.append(np.zeros(896, dtype="float32"))
            continue

        delta = curr - prev
        deltas.append(delta.cpu().numpy())

        if i % 50 == 0:
            print(f"delta {i}/500")

matrix = np.stack(deltas).astype("float32")
np.save(OUT, matrix)

print("shape:", matrix.shape)
print("saved:", OUT)

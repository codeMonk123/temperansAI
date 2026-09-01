from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import torch.nn.functional as F

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    output_hidden_states=True
)

sentences = [
    "Please cancel my subscription.",
    "Please do not cancel my subscription."
]

vectors = []

for sentence in sentences:

    inputs = tokenizer(sentence, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    tokens = tokenizer.convert_ids_to_tokens(
        inputs["input_ids"][0]
    )

    hidden = outputs.hidden_states[-1][0]

    for i, token in enumerate(tokens):

        if "cancel" in token:

            vectors.append(hidden[i])

            print("\nSentence:")
            print(sentence)

            print("Cancel token:")
            print(token)

similarity = F.cosine_similarity(
    vectors[0].unsqueeze(0),
    vectors[1].unsqueeze(0)
)

print("\nCosine similarity:")
print(similarity.item())

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

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

for sentence in sentences:

    inputs = tokenizer(sentence, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    print("\nSENTENCE:")
    print(sentence)

    print("\nTOKENS:")
    print(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0]))

    # Final transformer representation
    hidden = outputs.hidden_states[-1][0]

    # Find the token containing "cancel"
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

    for i, token in enumerate(tokens):
        if "cancel" in token:
            vector = hidden[i]

            print("\nCancel position:", i)
            print("Contextual vector shape:", vector.shape)

            print("First 10 contextual values:")
            print(vector[:10])

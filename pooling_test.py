import torch

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)


text = """
HUMAN: I want to cancel my subscription.
AI: Would you consider a 10 percent discount?
HUMAN: No thanks.
AI: What about 20 percent?
HUMAN: No.
AI: I can offer 30 percent.
HUMAN: I already said no.
AI: This is our best available offer.
HUMAN: No thanks.
"""


inputs = tokenizer(
    text,
    return_tensors="pt"
)


with torch.no_grad():

    outputs = model(**inputs)

    hidden = outputs.hidden_states[-1][0]


print("Hidden shape:")
print(hidden.shape)


# OLD METHOD
last_token_vector = hidden[-1]


# NEW METHOD
mean_vector = hidden.mean(dim=0)


print("\nLast-token vector shape:")
print(last_token_vector.shape)


print("\nMean-pooled vector shape:")
print(mean_vector.shape)


print("\nFirst 10 LAST-TOKEN values:")
print(last_token_vector[:10])


print("\nFirst 10 MEAN-POOLED values:")
print(mean_vector[:10])

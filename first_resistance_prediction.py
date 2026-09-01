import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


class ResistanceHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.linear = nn.Linear(896, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.linear(x))


print("Loading Qwen...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)

# Freeze Qwen.
for parameter in model.parameters():
    parameter.requires_grad = False


head = ResistanceHead()


text = "Human: No. Please cancel my subscription instead."

inputs = tokenizer(
    text,
    return_tensors="pt"
)


with torch.no_grad():

    outputs = model(**inputs)

    # Final transformer layer:
    #
    # shape:
    # [batch, tokens, 896]

    hidden_states = outputs.hidden_states[-1]


print("\nHidden-state shape:")
print(hidden_states.shape)


# For this first experiment, use the final token's
# contextual representation as the sentence representation.

sentence_vector = hidden_states[0, -1, :]


print("\nSentence-vector shape:")
print(sentence_vector.shape)


prediction = head(sentence_vector)


print("\nPredicted resistance:")
print(prediction.item())

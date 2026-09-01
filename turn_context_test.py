import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch.nn.functional as F

import torch.nn as nn


class ResistanceHead(nn.Module):

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(896, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.linear(x))

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

head = ResistanceHead()

head.load_state_dict(
    torch.load("temperans_resistance_head.pt")
)

head.eval()

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)


conversation_a = """
Agent: Would you like our discounted plan?
Human: No thanks.
"""


conversation_b = """
Human: I want to cancel my subscription.
Agent: Would you consider a 10 percent discount?
Human: No thanks.
Agent: What about 20 percent?
Human: No.
Agent: I can offer 30 percent.
Human: I already said no.
Agent: This is our best available offer.
Human: No thanks.
"""


def get_representation(text):

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    with torch.no_grad():

        outputs = model(**inputs)

    hidden = outputs.hidden_states[-1]

    # final token representation
    vector = hidden[0, -1, :]

    return vector


vector_a = get_representation(conversation_a)
vector_b = get_representation(conversation_b)


similarity = F.cosine_similarity(
    vector_a.unsqueeze(0),
    vector_b.unsqueeze(0)
)


print("Representation A shape:")
print(vector_a.shape)

print("\nRepresentation B shape:")
print(vector_b.shape)

print("\nCosine similarity:")
print(similarity.item())

with torch.no_grad():

    resistance_a = head(vector_a)
    resistance_b = head(vector_b)


print("\nConversation A resistance:")
print(resistance_a.item())

print("\nConversation B resistance:")
print(resistance_b.item())

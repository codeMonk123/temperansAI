import json

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


# Freeze every Qwen parameter
for parameter in model.parameters():
    parameter.requires_grad = False


head = ResistanceHead()


# Read our tiny Temperans dataset
examples = []

with open("temperans_train.jsonl", "r") as file:

    for line in file:

        example = json.loads(line)

        examples.append(example)


print("Training examples:", len(examples))


# Mean Squared Error
loss_function = nn.MSELoss()


# Optimizer changes ONLY the ResistanceHead
optimizer = torch.optim.Adam(
    head.parameters(),
    lr=0.001
)


# Train repeatedly over our 5 examples
for epoch in range(20):

    total_loss = 0.0

    for example in examples:

        text = example["text"]

        target = torch.tensor(
            [example["resistance"]],
            dtype=torch.float32
        )

        inputs = tokenizer(
            text,
            return_tensors="pt"
        )

        # Qwen is frozen
        with torch.no_grad():

            outputs = model(**inputs)

            hidden_states = outputs.hidden_states[-1]

            sentence_vector = hidden_states[0, -1, :]


        # Temperans prediction
        prediction = head(sentence_vector)


        # How wrong were we?
        loss = loss_function(
            prediction,
            target
        )


        # Remove old gradients
        optimizer.zero_grad()


        # Calculate how each weight contributed
        # to the error
        loss.backward()


        # Change the 897 weights
        optimizer.step()


        total_loss += loss.item()


    print(
        "Epoch:",
        epoch + 1,
        "Loss:",
        total_loss / len(examples)
    )


torch.save(
    head.state_dict(),
    "temperans_resistance_head.pt"
)

print("\nSaved model to temperans_resistance_head.pt")
print("\nTRAINING COMPLETE")

import json

import torch
import torch.nn as nn

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

TRAIN_FILE = "data/train/resistance_v1.jsonl"

OUTPUT_FILE = "temperans_resistance_v1.pt"


# ---------------------------------------------------------
# TEMPERANS RESISTANCE HEAD
# ---------------------------------------------------------

class ResistanceHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.linear = nn.Linear(896, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):

        return self.sigmoid(
            self.linear(x)
        )


# ---------------------------------------------------------
# BUILD REPRESENTATION FOR ONE TURN
# ---------------------------------------------------------

def get_turn_vector(
    example,
    tokenizer,
    model
):

    # ---------------------------------------------
    # Build history
    # ---------------------------------------------

    history_text = ""

    if example["history"]:

        history_text = "\n".join(
            example["history"]
        )

        history_text += "\n"


    # ---------------------------------------------
    # Current turn
    # ---------------------------------------------

    current_text = (
        "HUMAN: "
        + example["current_turn"]
    )


    full_text = (
        history_text
        + current_text
    )


    # ---------------------------------------------
    # Find where current turn starts
    # ---------------------------------------------

    history_ids = tokenizer(
        history_text,
        add_special_tokens=False
    )["input_ids"]


    current_start = len(
        history_ids
    )


    # ---------------------------------------------
    # Tokenize everything
    # ---------------------------------------------

    inputs = tokenizer(
        full_text,
        return_tensors="pt",
        add_special_tokens=False
    )


    # ---------------------------------------------
    # Run Qwen
    # ---------------------------------------------

    with torch.no_grad():

        outputs = model(**inputs)

        hidden = (
            outputs
            .hidden_states[-1][0]
        )


    # ---------------------------------------------
    # Keep current-turn tokens only
    # ---------------------------------------------

    current_hidden = hidden[
        current_start:
    ]


    # ---------------------------------------------
    # Mean pool current turn
    # ---------------------------------------------

    turn_vector = current_hidden.mean(
        dim=0
    )


    return turn_vector


# ---------------------------------------------------------
# LOAD TRAINING DATA
# ---------------------------------------------------------

examples = []

with open(
    TRAIN_FILE,
    "r"
) as file:

    for line in file:

        if line.strip():

            examples.append(
                json.loads(line)
            )


print(
    "Training examples:",
    len(examples)
)


# ---------------------------------------------------------
# LOAD QWEN
# ---------------------------------------------------------

print("Loading Qwen...")


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)


# Freeze Qwen.

for parameter in model.parameters():

    parameter.requires_grad = False


model.eval()


# ---------------------------------------------------------
# CREATE TEMPERANS HEAD
# ---------------------------------------------------------

head = ResistanceHead()


print(
    "Trainable Temperans parameters:",
    sum(
        p.numel()
        for p in head.parameters()
        if p.requires_grad
    )
)


# ---------------------------------------------------------
# PRECOMPUTE QWEN REPRESENTATIONS
# ---------------------------------------------------------

# Qwen is frozen.
#
# Therefore its representation for each training
# example will never change.
#
# We can calculate these vectors ONCE instead of
# running Qwen again during every epoch.


print(
    "\nCreating training representations..."
)


training_vectors = []


for example in examples:

    vector = get_turn_vector(
        example,
        tokenizer,
        model
    )

    target = torch.tensor(
        [example["resistance"]],
        dtype=torch.float32
    )

    training_vectors.append(
        (vector, target)
    )


print(
    "Representations created:",
    len(training_vectors)
)


# ---------------------------------------------------------
# TRAINING SETUP
# ---------------------------------------------------------

loss_function = nn.MSELoss()


optimizer = torch.optim.Adam(
    head.parameters(),
    lr=0.001
)


NUMBER_OF_EPOCHS = 50


# ---------------------------------------------------------
# TRAIN
# ---------------------------------------------------------

print("\nStarting training...")


for epoch in range(
    NUMBER_OF_EPOCHS
):

    total_loss = 0.0


    for vector, target in training_vectors:

        prediction = head(
            vector
        )


        loss = loss_function(
            prediction,
            target
        )


        optimizer.zero_grad()

        loss.backward()

        optimizer.step()


        total_loss += loss.item()


    average_loss = (
        total_loss
        / len(training_vectors)
    )


    print(
        "Epoch:",
        epoch + 1,
        "Loss:",
        round(
            average_loss,
            6
        )
    )


# ---------------------------------------------------------
# SAVE TEMPERANS WEIGHTS
# ---------------------------------------------------------

torch.save(
    head.state_dict(),
    OUTPUT_FILE
)


print(
    "\nSaved:",
    OUTPUT_FILE
)

print(
    "\nTRAINING COMPLETE"
)

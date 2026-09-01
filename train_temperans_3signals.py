import json

import torch
import torch.nn as nn

from transformers import AutoTokenizer, AutoModelForCausalLM


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

SIGNALS = [
    "resistance",
    "frustration",
    "intent_clarity"
]


# ---------------------------------------------------------
# TEMPERANS SIGNAL HEAD
# ---------------------------------------------------------

class TemperansHead(nn.Module):

    def __init__(self):
        super().__init__()

        # Qwen gives us a 896-dimensional representation.
        # We want 3 Temperans signals.
        self.linear = nn.Linear(896, 3)

        # Convert outputs into values between 0 and 1.
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):

        scores = self.linear(x)

        scores = self.sigmoid(scores)

        return scores


# ---------------------------------------------------------
# BUILD TEXT REPRESENTATION
# ---------------------------------------------------------

def build_texts(example):

    history_parts = []

    # Build conversation history.
    for turn in example["history"]:

        actor = turn["actor"].upper()
        text = turn["text"]

        history_parts.append(
            actor + ": " + text
        )

    history_text = "\n".join(history_parts)

    # Add newline between history and current turn.
    if history_text:
        history_text += "\n"


    # Build current turn.
    current = example["current_turn"]

    current_text = (
        current["actor"].upper()
        + ": "
        + current["text"]
    )


    # Complete conversation presented to Qwen.
    full_text = history_text + current_text


    return history_text, current_text, full_text


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


# ---------------------------------------------------------
# FREEZE QWEN
# ---------------------------------------------------------

# We are NOT training Qwen yet.
#
# Qwen's ~500M parameters remain unchanged.
# Only our small Temperans head will learn.

for parameter in model.parameters():

    parameter.requires_grad = False


model.eval()


# ---------------------------------------------------------
# CREATE TEMPERANS HEAD
# ---------------------------------------------------------

head = TemperansHead()


print("\nTemperans Head:")
print(head)


total_parameters = sum(
    p.numel()
    for p in head.parameters()
    if p.requires_grad
)


print(
    "\nTrainable Temperans parameters:",
    total_parameters
)


# ---------------------------------------------------------
# LOAD TEMPERANS DATASET
# ---------------------------------------------------------

examples = []

with open(
    "temperans_turns.jsonl",
    "r"
) as file:

    for line in file:

        # Ignore empty lines.
        if line.strip():

            example = json.loads(line)

            examples.append(example)


print(
    "\nTraining examples:",
    len(examples)
)


# ---------------------------------------------------------
# LOSS FUNCTION
# ---------------------------------------------------------

# Mean Squared Error:
#
# predicted signal vs correct signal
#
# Example:
#
# predicted frustration = 0.30
# target frustration    = 0.80
#
# MSE measures how far apart they are.

loss_function = nn.MSELoss()


# ---------------------------------------------------------
# OPTIMIZER
# ---------------------------------------------------------

# Adam changes ONLY the Temperans head parameters.

optimizer = torch.optim.Adam(
    head.parameters(),
    lr=0.001
)


# ---------------------------------------------------------
# TRAINING
# ---------------------------------------------------------

NUMBER_OF_EPOCHS = 30


for epoch in range(NUMBER_OF_EPOCHS):

    total_loss = 0.0


    for example in examples:

        # -------------------------------------------------
        # STEP 1:
        # Build history + current turn
        # -------------------------------------------------

        history_text, current_text, full_text = (
            build_texts(example)
        )


        # -------------------------------------------------
        # STEP 2:
        # Build correct Temperans target vector
        # -------------------------------------------------

        target = torch.tensor(
            [
                example["signals"]["resistance"],
                example["signals"]["frustration"],
                example["signals"]["intent_clarity"]
            ],
            dtype=torch.float32
        )


        # -------------------------------------------------
        # STEP 3:
        # Find where CURRENT TURN begins
        # -------------------------------------------------

        history_ids = tokenizer(
            history_text,
            add_special_tokens=False
        )["input_ids"]


        current_start = len(history_ids)


        # -------------------------------------------------
        # STEP 4:
        # Tokenize COMPLETE conversation
        # -------------------------------------------------

        inputs = tokenizer(
            full_text,
            return_tensors="pt",
            add_special_tokens=False
        )


        # -------------------------------------------------
        # STEP 5:
        # Run complete conversation through Qwen
        # -------------------------------------------------

        # Qwen is frozen, so we don't need gradients.

        with torch.no_grad():

            outputs = model(**inputs)

            # Final transformer layer.
            #
            # Shape:
            #
            # [batch, number_of_tokens, 896]

            hidden = outputs.hidden_states[-1][0]


        # -------------------------------------------------
        # STEP 6:
        # Select CURRENT TURN representations only
        # -------------------------------------------------

        current_hidden = hidden[
            current_start:
        ]


        # -------------------------------------------------
        # STEP 7:
        # Mean-pool CURRENT TURN
        # -------------------------------------------------

        # Every current-turn token has 896 numbers.
        #
        # Example:
        #
        # HUMAN     -> 896
        # :         -> 896
        # No        -> 896
        # thanks    -> 896
        #
        # Average them into ONE 896-dimensional vector.

        turn_vector = current_hidden.mean(
            dim=0
        )


        # -------------------------------------------------
        # STEP 8:
        # Temperans predicts 3 signals
        # -------------------------------------------------

        prediction = head(
            turn_vector
        )


        # -------------------------------------------------
        # STEP 9:
        # Compare prediction with correct answer
        # -------------------------------------------------

        loss = loss_function(
            prediction,
            target
        )


        # -------------------------------------------------
        # STEP 10:
        # TRAIN TEMPERANS HEAD
        # -------------------------------------------------

        # Clear gradients from previous step.
        optimizer.zero_grad()

        # Calculate gradients.
        loss.backward()

        # Change the 2,691 Temperans parameters.
        optimizer.step()


        total_loss += loss.item()


    # -----------------------------------------------------
    # EPOCH COMPLETE
    # -----------------------------------------------------

    average_loss = (
        total_loss
        / len(examples)
    )


    print(
        "Epoch:",
        epoch + 1,
        "Loss:",
        average_loss
    )


# ---------------------------------------------------------
# SAVE TEMPERANS WEIGHTS
# ---------------------------------------------------------

torch.save(
    head.state_dict(),
    "temperans_3signals.pt"
)


print(
    "\nSaved model to temperans_3signals.pt"
)

print(
    "\nTRAINING COMPLETE"
)

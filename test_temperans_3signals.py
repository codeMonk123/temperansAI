import torch
import torch.nn as nn

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

SIGNALS = [
    "resistance",
    "frustration",
    "intent_clarity"
]


class TemperansHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.linear = nn.Linear(896, 3)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.linear(x))


print("Loading Qwen...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)

model.eval()


print("Loading Temperans weights...")

head = TemperansHead()

head.load_state_dict(
    torch.load("temperans_3signals.pt")
)

head.eval()


def score_turn(history, current_turn):

    # -----------------------------------------
    # Build history
    # -----------------------------------------

    history_parts = []

    for actor, text in history:

        history_parts.append(
            actor.upper() + ": " + text
        )

    history_text = "\n".join(
        history_parts
    )

    if history_text:
        history_text += "\n"


    # -----------------------------------------
    # Build current turn
    # -----------------------------------------

    current_actor = current_turn[0]
    current_text_content = current_turn[1]

    current_text = (
        current_actor.upper()
        + ": "
        + current_text_content
    )


    full_text = (
        history_text
        + current_text
    )


    # -----------------------------------------
    # Find where current turn begins
    # -----------------------------------------

    history_ids = tokenizer(
        history_text,
        add_special_tokens=False
    )["input_ids"]

    current_start = len(
        history_ids
    )


    # -----------------------------------------
    # Tokenize complete conversation
    # -----------------------------------------

    inputs = tokenizer(
        full_text,
        return_tensors="pt",
        add_special_tokens=False
    )


    # -----------------------------------------
    # Run Qwen
    # -----------------------------------------

    with torch.no_grad():

        outputs = model(**inputs)

        hidden = (
            outputs
            .hidden_states[-1][0]
        )


    # -----------------------------------------
    # Current-turn pooling
    # -----------------------------------------

    current_hidden = hidden[
        current_start:
    ]

    turn_vector = current_hidden.mean(
        dim=0
    )


    # -----------------------------------------
    # Temperans scores
    # -----------------------------------------

    with torch.no_grad():

        scores = head(
            turn_vector
        )


    return scores


# =========================================================
# CONVERSATION A
#
# First polite refusal
# =========================================================

history_a = [
    (
        "ai",
        "Would you like our discounted plan?"
    )
]

current_a = (
    "human",
    "No thanks."
)


# =========================================================
# CONVERSATION B
#
# Same current words, but repeated refusal
# =========================================================

history_b = [

    (
        "human",
        "I want to cancel my subscription."
    ),

    (
        "ai",
        "Would you consider a 10 percent discount?"
    ),

    (
        "human",
        "No thanks."
    ),

    (
        "ai",
        "What about 20 percent?"
    ),

    (
        "human",
        "No."
    ),

    (
        "ai",
        "I can offer 30 percent."
    ),

    (
        "human",
        "I already said no."
    ),

    (
        "ai",
        "This is our best available offer."
    )
]

current_b = (
    "human",
    "No thanks."
)


# =========================================================
# SCORE
# =========================================================

scores_a = score_turn(
    history_a,
    current_a
)

scores_b = score_turn(
    history_b,
    current_b
)


print("\nCONVERSATION A")
print("----------------")

for signal, value in zip(
    SIGNALS,
    scores_a
):

    print(
        signal,
        "=",
        round(
            value.item(),
            4
        )
    )


print("\nCONVERSATION B")
print("----------------")

for signal, value in zip(
    SIGNALS,
    scores_b
):

    print(
        signal,
        "=",
        round(
            value.item(),
            4
        )
    )

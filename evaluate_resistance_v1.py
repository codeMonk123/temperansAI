import json

import torch
import torch.nn as nn

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

TEST_FILE = "data/test/resistance_test_cases.jsonl"

WEIGHTS_FILE = "temperans_resistance_v1.pt"


# ---------------------------------------------------------
# TEMPERANS HEAD
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
# TURN REPRESENTATION
# ---------------------------------------------------------

def get_turn_vector(
    example,
    tokenizer,
    model
):

    history_text = ""

    if example["history"]:

        history_text = "\n".join(
            example["history"]
        )

        history_text += "\n"


    current_text = (
        "HUMAN: "
        + example["current_turn"]
    )


    full_text = (
        history_text
        + current_text
    )


    history_ids = tokenizer(
        history_text,
        add_special_tokens=False
    )["input_ids"]


    current_start = len(
        history_ids
    )


    inputs = tokenizer(
        full_text,
        return_tensors="pt",
        add_special_tokens=False
    )


    with torch.no_grad():

        outputs = model(**inputs)

        hidden = (
            outputs
            .hidden_states[-1][0]
        )


    current_hidden = hidden[
        current_start:
    ]


    turn_vector = current_hidden.mean(
        dim=0
    )


    return turn_vector


# ---------------------------------------------------------
# LOAD TEST DATA
# ---------------------------------------------------------

test_cases = []

with open(
    TEST_FILE,
    "r"
) as file:

    for line in file:

        if line.strip():

            test_cases.append(
                json.loads(line)
            )


print(
    "Test examples:",
    len(test_cases)
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


model.eval()


# ---------------------------------------------------------
# LOAD TEMPERANS
# ---------------------------------------------------------

head = ResistanceHead()


head.load_state_dict(
    torch.load(
        WEIGHTS_FILE
    )
)


head.eval()


print(
    "Loaded Temperans weights."
)


# ---------------------------------------------------------
# EVALUATE
# ---------------------------------------------------------

absolute_errors = []


print("\nRESULTS")
print("=======")


for case in test_cases:

    vector = get_turn_vector(
        case,
        tokenizer,
        model
    )


    with torch.no_grad():

        prediction = head(
            vector
        ).item()


    expected = case[
        "expected_resistance"
    ]


    error = abs(
        prediction - expected
    )


    absolute_errors.append(
        error
    )


    print(
        "\nCase:",
        case["id"]
    )

    print(
        "Current:",
        case["current_turn"]
    )

    print(
        "Expected:",
        expected
    )

    print(
        "Temperans:",
        round(
            prediction,
            4
        )
    )

    print(
        "Error:",
        round(
            error,
            4
        )
    )


# ---------------------------------------------------------
# MAE
# ---------------------------------------------------------

mae = sum(
    absolute_errors
) / len(
    absolute_errors
)


print(
    "\n=========================="
)

print(
    "TEMPERANS V1 MAE:",
    round(
        mae,
        4
    )
)

print(
    "QWEN BASELINE MAE: 0.3713"
)

print(
    "=========================="
)


# ---------------------------------------------------------
# IMPROVEMENT
# ---------------------------------------------------------

baseline = 0.3713


improvement = (
    baseline - mae
)


percentage_improvement = (
    improvement / baseline
) * 100


print(
    "\nAbsolute improvement:",
    round(
        improvement,
        4
    )
)

print(
    "Relative improvement:",
    round(
        percentage_improvement,
        2
    ),
    "%"
)

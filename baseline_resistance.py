import json
import re

import torch

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


# ---------------------------------------------------------
# LOAD QWEN
# ---------------------------------------------------------

print("Loading Qwen...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME
)

model.eval()


# ---------------------------------------------------------
# LOAD TEST CASES
# ---------------------------------------------------------

cases = []

with open(
    "resistance_test_cases.jsonl",
    "r"
) as file:

    for line in file:

        if line.strip():
            cases.append(
                json.loads(line)
            )


print("Test cases:", len(cases))


# ---------------------------------------------------------
# SCORE ONE CASE
# ---------------------------------------------------------

def score_case(case):

    history = "\n".join(
        case["history"]
    )

    prompt = f"""
Resistance means the degree to which the CURRENT ACTOR
opposes, rejects, refuses, or pushes back against another
actor's proposed action, request, position, or direction.

Use this scale:

0.00 = no resistance
0.25 = mild hesitation
0.50 = clear disagreement or refusal
0.75 = strong or repeated refusal
1.00 = persistent and unequivocal resistance after repeated attempts

Rules:

- Score the current turn, not the whole conversation.
- Use previous history when it changes the meaning.
- Repeated refusal should generally score higher than a first refusal.
- Do not infer resistance only from words such as "no" or "not".
- Resistance is different from frustration.
- Resistance is different from uncertainty.

HISTORY:
{history if history else "(none)"}

CURRENT TURN:
{case["current_turn"]}

Return ONLY one decimal number between 0.0 and 1.0.
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=10,
            do_sample=False
        )


    generated = outputs[0][
        inputs["input_ids"].shape[1]:
    ]


    answer = tokenizer.decode(
        generated,
        skip_special_tokens=True
    ).strip()


    # Try to extract a number from Qwen's answer.

    match = re.search(
        r"(?:0(?:\.\d+)?|1(?:\.0+)?)",
        answer
    )


    if match:

        prediction = float(
            match.group()
        )

    else:

        prediction = None


    return prediction, answer


# ---------------------------------------------------------
# RUN BASELINE
# ---------------------------------------------------------

absolute_errors = []


print("\nRESULTS")
print("=======")


for case in cases:

    prediction, raw_answer = score_case(
        case
    )

    expected = case[
        "expected_resistance"
    ]


    print("\nCase:", case["id"])

    print(
        "Current turn:",
        case["current_turn"]
    )

    print(
        "Expected:",
        expected
    )

    print(
        "Qwen prediction:",
        prediction
    )

    print(
        "Raw answer:",
        raw_answer
    )


    if prediction is not None:

        error = abs(
            prediction - expected
        )

        absolute_errors.append(
            error
        )

        print(
            "Absolute error:",
            round(error, 4)
        )


# ---------------------------------------------------------
# OVERALL ERROR
# ---------------------------------------------------------

if absolute_errors:

    mae = sum(
        absolute_errors
    ) / len(
        absolute_errors
    )

    print("\n======================")

    print(
        "BASELINE MAE:",
        round(mae, 4)
    )

    print("======================")

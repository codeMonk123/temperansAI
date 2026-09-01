import json


with open("temperans_turns.jsonl", "r") as file:
    first_line = file.readline()
    example = json.loads(first_line)


history = example["history"]
current_turn = example["current_turn"]


parts = []

for turn in history:

    actor = turn["actor"].upper()
    text = turn["text"]

    parts.append(
        actor + ": " + text
    )


current_actor = current_turn["actor"].upper()
current_text = current_turn["text"]

parts.append(
    current_actor + ": " + current_text
)


model_input = "\n".join(parts)


print("MODEL INPUT:")
print("------------")
print(model_input)

print("\nTARGET SIGNALS:")
print("---------------")

for signal, value in example["signals"].items():
    print(signal, "=", value)

import json

examples = []

with open("temperans_train.jsonl", "r") as file:
    for line in file:
        example = json.loads(line)
        examples.append(example)

print("Number of examples:", len(examples))

for i, example in enumerate(examples):
    print("\nExample", i + 1)
    print("Text:", example["text"])
    print("Resistance:", example["resistance"])

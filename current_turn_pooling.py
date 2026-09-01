import torch

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)


history = """
HUMAN: I want to cancel my subscription.
AI: Would you consider a 10 percent discount?
HUMAN: No thanks.
AI: What about 20 percent?
HUMAN: No.
AI: I can offer 30 percent.
"""

current_turn = """
HUMAN: I already said no.
"""


full_text = history + current_turn


# Tokenize history separately so we know
# where the current turn begins.

history_ids = tokenizer(
    history,
    add_special_tokens=False
)["input_ids"]


inputs = tokenizer(
    full_text,
    return_tensors="pt",
    add_special_tokens=False
)


current_start = len(history_ids)


with torch.no_grad():

    outputs = model(**inputs)

    hidden = outputs.hidden_states[-1][0]


# Take ONLY contextualized representations
# belonging to the current turn.

current_hidden = hidden[current_start:]


# Average the current-turn token representations.

turn_vector = current_hidden.mean(dim=0)


print("Total tokens:")
print(hidden.shape[0])

print("\nHistory tokens:")
print(current_start)

print("\nCurrent-turn tokens:")
print(current_hidden.shape[0])

print("\nTurn-vector shape:")
print(turn_vector.shape)

print("\nCurrent-turn tokens:")

current_ids = inputs["input_ids"][0][current_start:]

print(
    tokenizer.convert_ids_to_tokens(current_ids)
)

print("\nFirst 10 turn-vector values:")
print(turn_vector[:10])

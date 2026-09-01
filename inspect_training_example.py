from transformers import AutoTokenizer

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)

text = "Human: No. Please cancel my subscription instead."

token_ids = tokenizer.encode(text)

print("TEXT:")
print(text)

print("\nTOKEN IDs:")
print(token_ids)

print("\nNUMBER OF TOKENS:")
print(len(token_ids))

print("\nDECODE EACH TOKEN:")

for token_id in token_ids:
    print(token_id, "->", repr(tokenizer.decode([token_id])))

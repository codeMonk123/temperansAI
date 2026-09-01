from transformers import AutoTokenizer

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)

text = "The agent is becoming increasingly manipulative and uncooperative."

tokens = tokenizer.tokenize(text)
token_ids = tokenizer.encode(text)

print("Original text:")
print(text)

print("\nTokens:")
print(tokens)

print("\nToken IDs:")
print(token_ids)


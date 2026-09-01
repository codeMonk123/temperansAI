from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

token_id = tokenizer.encode(" cancel", add_special_tokens=False)[0]

print("Token ID:")
print(token_id)

embedding_layer = model.get_input_embeddings()

print("\nEmbedding table shape:")
print(embedding_layer.weight.shape)

embedding = embedding_layer.weight[token_id]

print("\nEmbedding shape:")
print(embedding.shape)

print("\nFirst 20 numbers of the embedding:")
print(embedding[:20])

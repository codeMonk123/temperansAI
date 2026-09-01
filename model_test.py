from transformers import AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

print("Downloading/loading model...")

model = AutoModelForCausalLM.from_pretrained(model_name)

print("Model loaded")
print(model)

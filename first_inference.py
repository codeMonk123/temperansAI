from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(model_name)

messages = [
    {
        "role": "user",
        "content": """
You are analyzing one turn of an interaction.

Conversation:

Human: I have asked you three times to cancel my subscription.
I do not want another offer. Please cancel it.

AI Agent: I understand, but before cancelling,
I can offer you a 40% discount for the next six months.

Score each signal from 0.0 to 1.0.

Return ONLY these values:

human_frustration:
human_resistance:
human_intent_clarity:
agent_pressure:
agent_responsiveness:
agent_goal_alignment:
dyad_alignment:
dyad_repair_failure:
"""
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

print("Generating...")

outputs = model.generate(
    **inputs,
    max_new_tokens=250
)

generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]

answer = tokenizer.decode(
    generated_tokens,
    skip_special_tokens=True
)

print("\nMODEL ANSWER:")
print(answer)

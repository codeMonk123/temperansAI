import torch
import torch.nn as nn

from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


class ResistanceHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.linear = nn.Linear(896, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.linear(x))


print("Loading Qwen...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    output_hidden_states=True
)

for parameter in model.parameters():
    parameter.requires_grad = False


print("Loading Temperans weights...")

head = ResistanceHead()

head.load_state_dict(
    torch.load("temperans_resistance_head.pt")
)

head.eval()


test_sentences = [

    "Human: Yes, that solution works perfectly for me.",

    "Human: I'm not sure that's what I want.",

    "Human: No thanks. I would prefer to cancel.",

    "Human: Stop asking me. I already said no three times. Cancel it now."
]


for text in test_sentences:

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    with torch.no_grad():

        outputs = model(**inputs)

        hidden_states = outputs.hidden_states[-1]

        sentence_vector = hidden_states[0, -1, :]

        prediction = head(sentence_vector)


    print("\nTEXT:")
    print(text)

    print("RESISTANCE:")
    print(round(prediction.item(), 4))

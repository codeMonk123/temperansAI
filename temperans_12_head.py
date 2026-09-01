import torch
import torch.nn as nn


SIGNALS = [
    "resistance",
    "frustration",
    "uncertainty",
    "intent_clarity",
    "alignment",
    "repetition",
    "pressure",
    "repair_failure",
    "trust_erosion",
    "escalation_likelihood",
    "cross_surface_repetition",
    "effort_duplication"
]


class TemperansHead(nn.Module):

    def __init__(self):
        super().__init__()

        # Qwen representation:
        # 896 dimensions
        #
        # Temperans output:
        # 12 behavioral signals

        self.linear = nn.Linear(
            896,
            len(SIGNALS)
        )

        self.sigmoid = nn.Sigmoid()


    def forward(self, x):

        scores = self.linear(x)

        scores = self.sigmoid(scores)

        return scores


head = TemperansHead()


print("Temperans Head:")
print(head)


print("\nSignals:")
for index, signal in enumerate(SIGNALS):
    print(index, "->", signal)


print("\nWeight shape:")
print(head.linear.weight.shape)


print("\nBias shape:")
print(head.linear.bias.shape)


total_parameters = sum(
    parameter.numel()
    for parameter in head.parameters()
    if parameter.requires_grad
)


print("\nTrainable parameters:")
print(total_parameters)

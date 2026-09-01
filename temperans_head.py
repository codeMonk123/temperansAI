import torch
import torch.nn as nn


class TemperansHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.linear = nn.Linear(896, 3)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):

        scores = self.linear(x)
        scores = self.sigmoid(scores)

        return scores


head = TemperansHead()


print(head)

print("\nWeight shape:")
print(head.linear.weight.shape)

print("\nBias shape:")
print(head.linear.bias.shape)

print("\nNumber of trainable parameters:")

total = sum(
    p.numel()
    for p in head.parameters()
    if p.requires_grad
)

print(total)

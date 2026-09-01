import torch
import torch.nn as nn


class ResistanceHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.linear = nn.Linear(896, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):

        score = self.linear(x)
        score = self.sigmoid(score)

        return score


head = ResistanceHead()

print(head)

print("\nWeight shape:")
print(head.linear.weight.shape)

print("\nBias shape:")
print(head.linear.bias.shape)

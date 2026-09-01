import torch
import torch.nn as nn


class ResistanceHead(nn.Module):

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(896, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.linear(x))


head = ResistanceHead()

head.load_state_dict(
    torch.load("temperans_resistance_head.pt")
)

weights = head.linear.weight[0]
bias = head.linear.bias[0]


print("Number of learned weights:")
print(len(weights))

print("\nFirst 20 learned weights:")
print(weights[:20])

print("\nLearned bias:")
print(bias)

print("\nLargest weight:")
print(torch.max(weights))

print("\nSmallest weight:")
print(torch.min(weights))

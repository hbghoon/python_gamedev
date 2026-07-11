"""
MNIST digit classifier in PyTorch — a learning example.

Pipeline:
  1. Load the MNIST dataset (28x28 grayscale images of digits 0-9).
  2. Define a small Convolutional Neural Network (CNN).
  3. Train it for a few epochs.
  4. Evaluate accuracy on the test set.
  5. Save the trained weights.

Run:  python mnist.py
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


# ---------------------------------------------------------------------------
# 1. Device: use a GPU if one is available, otherwise the CPU.
# ---------------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


# ---------------------------------------------------------------------------
# 2. Data loading.
#    transforms.ToTensor()  -> converts a PIL image to a tensor in [0, 1].
#    transforms.Normalize() -> shifts/scales to roughly mean 0, std 1.
#       (0.1307, 0.3081) are the precomputed mean/std of MNIST.
# ---------------------------------------------------------------------------
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,)),
])

# download=True will fetch the dataset into ./data the first time you run this.
train_dataset = datasets.MNIST(root="./data", train=True,  download=True, transform=transform)
test_dataset  = datasets.MNIST(root="./data", train=False, download=True, transform=transform)

# DataLoader batches the data and shuffles it (for training).
train_loader = DataLoader(train_dataset, batch_size=64,  shuffle=True)
test_loader  = DataLoader(test_dataset,  batch_size=1000, shuffle=False)


# ---------------------------------------------------------------------------
# 3. The model: a simple CNN.
#    Input shape:  (batch, 1, 28, 28)   — 1 channel (grayscale).
#    Output shape: (batch, 10)          — one score per digit class.
# ---------------------------------------------------------------------------
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        # Conv layers extract spatial features.
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3)   # 28x28 -> 26x26
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)  # 26x26 -> 24x24
        self.dropout = nn.Dropout(0.25)                # helps prevent overfitting
        # Fully connected layers do the final classification.
        # After conv2 + 2x2 pooling the feature map is 64 x 12 x 12 = 9216.
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)        # 24x24 -> 12x12
        x = self.dropout(x)
        x = torch.flatten(x, 1)       # flatten everything except the batch dim
        x = F.relu(self.fc1(x))
        x = self.fc2(x)               # raw scores (logits); no softmax needed here
        return x


model = Net().to(device)

# Adam is a good default optimizer for getting started.
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
# CrossEntropyLoss expects raw logits + integer class labels.
criterion = nn.CrossEntropyLoss()


# ---------------------------------------------------------------------------
# 4. Training loop.
# ---------------------------------------------------------------------------
def train(epoch):
    model.train()  # put the model in "training mode" (enables dropout, etc.)
    for batch_idx, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()          # clear gradients from the previous step
        outputs = model(images)        # forward pass
        loss = criterion(outputs, labels)
        loss.backward()                # backprop: compute gradients
        optimizer.step()               # update the weights

        if batch_idx % 100 == 0:
            print(f"Epoch {epoch} [{batch_idx * len(images):5d}/{len(train_loader.dataset)}]  "
                  f"loss: {loss.item():.4f}")


# ---------------------------------------------------------------------------
# 5. Evaluation (no gradient tracking needed).
# ---------------------------------------------------------------------------
def test():
    model.eval()  # "evaluation mode" (disables dropout)
    test_loss = 0
    correct = 0
    with torch.no_grad():  # don't track gradients -> faster, less memory
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            test_loss += criterion(outputs, labels).item()
            preds = outputs.argmax(dim=1)               # pick the highest-scoring class
            correct += (preds == labels).sum().item()

    test_loss /= len(test_loader)
    accuracy = 100.0 * correct / len(test_loader.dataset)
    print(f"\nTest set: avg loss {test_loss:.4f}, "
          f"accuracy {correct}/{len(test_loader.dataset)} ({accuracy:.2f}%)\n")


# ---------------------------------------------------------------------------
# 6. Run it.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    EPOCHS = 3  # MNIST gets ~99% quickly; bump this up to experiment.
    for epoch in range(1, EPOCHS + 1):
        train(epoch)
        test()

    torch.save(model.state_dict(), "mnist_cnn.pt")
    print("Saved trained model to mnist_cnn.pt")

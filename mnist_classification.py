import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import pandas as pd
from sklearn.metrics import confusion_matrix

# Set device (GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Hyperparameters
batch_size = 64
learning_rate = 0.001
num_epochs = 5

# MNIST dataset and data loaders
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])
train_dataset = torchvision.datasets.MNIST(root='./data', train=True, download=True, transform=transform)
test_dataset = torchvision.datasets.MNIST(root='./data', train=False, download=True, transform=transform)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)


# Define a simple CNN model for MNIST
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))  # [batch, 32, 14, 14]
        x = self.pool(F.relu(self.conv2(x)))  # [batch, 64, 7, 7]
        x = x.view(-1, 64 * 7 * 7)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


model = SimpleCNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# Lists to store training and validation metrics
training_metrics = []
validation_metrics = []
all_preds = []
all_labels = []

# Training and validation loop
for epoch in range(num_epochs):
    model.train()
    train_loss = 0
    train_correct = 0
    total_train = 0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        total_train += labels.size(0)
        train_correct += (predicted == labels).sum().item()

    train_loss /= total_train
    train_accuracy = train_correct / total_train

    # Validation
    model.eval()
    val_loss = 0
    val_correct = 0
    total_val = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            total_val += labels.size(0)
            val_correct += (predicted == labels).sum().item()
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    val_loss /= total_val
    val_accuracy = val_correct / total_val

    training_metrics.append({"epoch": epoch + 1, "loss": train_loss, "accuracy": train_accuracy})
    validation_metrics.append({"epoch": epoch + 1, "loss": val_loss, "accuracy": val_accuracy})
    print(
        f"Epoch {epoch + 1}/{num_epochs} - Train Loss: {train_loss:.4f}, Train Acc: {train_accuracy:.4f} | Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}")

# Save metrics to CSV files
pd.DataFrame(training_metrics).to_csv("train_metrics.csv", index=False)
pd.DataFrame(validation_metrics).to_csv("val_metrics.csv", index=False)

# Compute and save confusion matrix
conf_mat = confusion_matrix(all_labels, all_preds)
conf_mat_df = pd.DataFrame(conf_mat,
                           index=[f"True {i}" for i in range(10)],
                           columns=[f"Pred {i}" for i in range(10)])
conf_mat_df.to_csv("confusion_matrix.csv")
print("Training complete. Metrics saved to train_metrics.csv, val_metrics.csv, and confusion_matrix.csv.")
import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path

# python 01_research/01_mlp.py

# 재현성을 위한 시드
np.random.seed(42)
torch.manual_seed(42)

# 1. 데이터 생성
X, y = make_moons(
    n_samples=2000,
    noise=0.15,
    random_state=42
)

# 2. 학습/테스트 데이터 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 3. 입력 정규화
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 4. PyTorch 텐서 변환
X_train_t = torch.tensor(X_train, dtype=torch.float32)
y_train_t = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)

X_test_t = torch.tensor(X_test, dtype=torch.float32)
y_test_t = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)

# 5. MLP 정의
class SquareMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(2, 4)
        self.fc2 = nn.Linear(4, 1)

    def forward(self, x):
        x = self.fc1(x)
        x = x * x
        x = self.fc2(x)
        return x

model = SquareMLP()

# 6. 학습 설정
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

loader = DataLoader(
    TensorDataset(X_train_t, y_train_t),
    batch_size=64,
    shuffle=True
)

# 7. 학습
for epoch in range(300):
    model.train()

    for xb, yb in loader:
        optimizer.zero_grad()

        logits = model(xb)
        loss = criterion(logits, yb)

        loss.backward()
        optimizer.step()

    if (epoch + 1) % 50 == 0:
        print(f"Epoch {epoch + 1}, Loss: {loss.item():.4f}")

# 8. 평문 정확도 평가
model.eval()

with torch.no_grad():
    logits = model(X_test_t)
    predictions = (logits >= 0).float()
    accuracy = (predictions == y_test_t).float().mean().item()

print(f"Plaintext Accuracy: {accuracy:.4f}")

# 9. 가중치 저장
output_dir = Path(__file__).parent / "results"
output_dir.mkdir(parents=True, exist_ok=True)

np.savez(
    output_dir / "mlp_model.npz",
    W1=model.fc1.weight.detach().numpy(),
    b1=model.fc1.bias.detach().numpy(),
    W2=model.fc2.weight.detach().numpy(),
    b2=model.fc2.bias.detach().numpy(),
    X_test=X_test,
    y_test=y_test,
    mean=scaler.mean_,
    scale=scaler.scale_,
)

print("Model and test data saved.")
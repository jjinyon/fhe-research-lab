import numpy as np
import torch
import torch.nn as nn

from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split

from openfhe import *

# python 02_research/01_ckks_error_ex.py


# ============================================================
# 1. Reproducibility
# ============================================================

np.random.seed(42)
torch.manual_seed(42)


# ============================================================
# 2. Dataset
# ============================================================

X, y = make_moons(
    n_samples=1000,
    noise=0.10,
    random_state=42
)

X = torch.tensor(X, dtype=torch.float32)
y = torch.tensor(y, dtype=torch.float32).reshape(-1, 1)


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# ============================================================
# 3. MLP
#
# Input : 2
# Hidden: 8
# Output: 1
#
# Activation:
#     x^2
#
# This is intentionally polynomial so that
# it can be evaluated using CKKS.
# ============================================================

class SquareMLP(nn.Module):

    def __init__(self):

        super().__init__()

        self.fc1 = nn.Linear(2, 8)
        self.fc2 = nn.Linear(8, 1)

    def forward(self, x):

        x = self.fc1(x)

        # Polynomial activation
        x = x * x

        x = self.fc2(x)

        return x


model = SquareMLP()


# ============================================================
# 4. Train plaintext model
# ============================================================

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.01
)


print("=" * 60)
print("PLAINTEXT TRAINING")
print("=" * 60)


for epoch in range(300):

    optimizer.zero_grad()

    logits = model(X_train)

    loss = criterion(
        logits,
        y_train
    )

    loss.backward()

    optimizer.step()

    if (epoch + 1) % 50 == 0:

        print(
            f"Epoch {epoch + 1:3d} | "
            f"Loss = {loss.item():.8f}"
        )


# ============================================================
# 5. Plaintext inference
# ============================================================

with torch.no_grad():

    plain_logits = (
        model(X_test)
        .numpy()
        .flatten()
    )


plain_labels = y_test.numpy().flatten().astype(int)

plain_predictions = (
    plain_logits >= 0
).astype(int)


plain_accuracy = np.mean(
    plain_predictions == plain_labels
)


print()
print("=" * 60)
print("PLAINTEXT INFERENCE")
print("=" * 60)

print(
    f"Plaintext accuracy: "
    f"{plain_accuracy:.6f}"
)


# ============================================================
# 6. Extract model parameters
# ============================================================

W1 = (
    model.fc1.weight
    .detach()
    .numpy()
)

b1 = (
    model.fc1.bias
    .detach()
    .numpy()
)

W2 = (
    model.fc2.weight
    .detach()
    .numpy()
)

b2 = (
    model.fc2.bias
    .detach()
    .numpy()
)


print()
print("Model shape:")
print("W1:", W1.shape)
print("b1:", b1.shape)
print("W2:", W2.shape)
print("b2:", b2.shape)


# ============================================================
# 7. CKKS parameters
# ============================================================

parameters = CCParamsCKKSRNS()

# We use a little more depth than mathematically necessary
# to leave enough room for CKKS level consumption.
parameters.SetMultiplicativeDepth(4)

# Precision of CKKS scaling factor
parameters.SetScalingModSize(50)

# Two input features are packed into two slots.
parameters.SetBatchSize(2)


cc = GenCryptoContext(parameters)


# ============================================================
# 8. Enable required operations
# ============================================================

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)
cc.Enable(ADVANCEDSHE)


print()
print("=" * 60)
print("CKKS CONTEXT")
print("=" * 60)

print(
    "Ring dimension:",
    cc.GetRingDimension()
)


# ============================================================
# 9. Key generation
# ============================================================

keys = cc.KeyGen()

public_key = keys.publicKey
secret_key = keys.secretKey


# Required for ciphertext-ciphertext multiplication.
# We use this for z * z.
cc.EvalMultKeyGen(secret_key)


# Required for EvalSum.
# We use this to calculate:
#
#     w1*x1 + w2*x2
#
# from packed slots.
cc.EvalSumKeyGen(secret_key)


# ============================================================
# 10. CKKS encrypted inference
# ============================================================

def ckks_predict(x):

    """
    x = [x1, x2]

    Packed ciphertext:

        [x1, x2]

    For each hidden neuron i:

        z_i = w_i1*x1 + w_i2*x2 + b_i

    We compute the weighted sum homomorphically.

    Then:

        h_i = z_i^2

    Finally:

        y = sum(W2_i * h_i) + b2
    """


    # --------------------------------------------------------
    # Encode input
    # --------------------------------------------------------

    plaintext_x = cc.MakeCKKSPackedPlaintext(
        [
            float(x[0]),
            float(x[1])
        ]
    )


    # --------------------------------------------------------
    # Encrypt input
    # --------------------------------------------------------

    ciphertext_x = cc.Encrypt(
        public_key,
        plaintext_x
    )


    # --------------------------------------------------------
    # First linear layer
    #
    # z_i = w_i1*x1 + w_i2*x2 + b_i
    # --------------------------------------------------------

    hidden_ciphertexts = []


    for i in range(8):

        # Weight vector for this neuron.
        #
        # Example:
        #
        # [w_i1, w_i2]
        #
        weight_plaintext = (
            cc.MakeCKKSPackedPlaintext(
                [
                    float(W1[i, 0]),
                    float(W1[i, 1])
                ]
            )
        )


        # Homomorphic multiplication:
        #
        # [x1, x2] * [w_i1, w_i2]
        #
        # =
        #
        # [w_i1*x1, w_i2*x2]
        weighted = cc.EvalMult(
            ciphertext_x,
            weight_plaintext
        )


        # Homomorphic sum:
        #
        # w_i1*x1 + w_i2*x2
        #
        summed = cc.EvalSum(
            weighted,
            2
        )


        # Add bias.
        #
        # z_i = weighted_sum + b_i
        #
        z = cc.EvalAdd(
            summed,
            float(b1[i])
        )


        hidden_ciphertexts.append(z)


    # --------------------------------------------------------
    # Square activation
    #
    # h_i = z_i^2
    #
    # This is ciphertext-ciphertext multiplication.
    # --------------------------------------------------------

    activated = []


    for z in hidden_ciphertexts:

        h = cc.EvalMult(
            z,
            z
        )

        activated.append(h)


    # --------------------------------------------------------
    # Output layer
    #
    # y = sum(W2_i * h_i) + b2
    # --------------------------------------------------------

    output = None


    for i in range(8):

        weighted_output = cc.EvalMult(
            activated[i],
            float(W2[0, i])
        )


        if output is None:

            output = weighted_output

        else:

            output = cc.EvalAdd(
                output,
                weighted_output
            )


    output = cc.EvalAdd(
        output,
        float(b2[0])
    )


    # --------------------------------------------------------
    # Decryption
    #
    # IMPORTANT:
    #
    # This is the FIRST decryption.
    #
    # Everything above was done while encrypted.
    # --------------------------------------------------------

    decrypted = cc.Decrypt(
        secret_key,
        output
    )


    decrypted.SetLength(1)


    result = (
        decrypted
        .GetRealPackedValue()[0]
    )


    return float(result)


# ============================================================
# 11. Run CKKS inference
# ============================================================

print()
print("=" * 60)
print("CKKS INFERENCE")
print("=" * 60)


ckks_logits = []


for i, x in enumerate(X_test.numpy()):

    result = ckks_predict(x)

    ckks_logits.append(result)


    if (i + 1) % 20 == 0:

        print(
            f"Processed "
            f"{i + 1:3d}/{len(X_test)}"
        )


ckks_logits = np.array(
    ckks_logits
)


# ============================================================
# 12. CKKS predictions
# ============================================================

ckks_predictions = (
    ckks_logits >= 0
).astype(int)


ckks_accuracy = np.mean(
    ckks_predictions == plain_labels
)


# ============================================================
# 13. Numerical error
# ============================================================

errors = (
    ckks_logits -
    plain_logits
)

absolute_errors = np.abs(
    errors
)


mae = np.mean(
    absolute_errors
)


rmse = np.sqrt(
    np.mean(
        errors ** 2
    )
)


max_error = np.max(
    absolute_errors
)


# ============================================================
# 14. Prediction changes
# ============================================================

prediction_changed = (
    plain_predictions !=
    ckks_predictions
)


num_prediction_changes = np.sum(
    prediction_changed
)


# ============================================================
# 15. Final results
# ============================================================

print()
print("=" * 60)
print("FINAL RESULTS")
print("=" * 60)


print(
    f"Plaintext Accuracy : "
    f"{plain_accuracy:.6f}"
)


print(
    f"CKKS Accuracy      : "
    f"{ckks_accuracy:.6f}"
)


print(
    f"Accuracy Difference: "
    f"{ckks_accuracy - plain_accuracy:+.6f}"
)


print()

print(
    f"MAE                : "
    f"{mae:.10e}"
)


print(
    f"RMSE               : "
    f"{rmse:.10e}"
)


print(
    f"Maximum Error      : "
    f"{max_error:.10e}"
)


print()

print(
    f"Prediction Changes : "
    f"{num_prediction_changes}"
    f"/{len(X_test)}"
)


# ============================================================
# 16. Samples whose predictions changed
# ============================================================

changed_indices = np.where(
    prediction_changed
)[0]


print()
print("=" * 60)
print("PREDICTION CHANGES")
print("=" * 60)


if len(changed_indices) == 0:

    print(
        "No prediction changed "
        "between plaintext and CKKS."
    )

else:

    for idx in changed_indices:

        print()
        print(
            f"Sample {idx}"
        )

        print(
            f"Plain logit : "
            f"{plain_logits[idx]: .10e}"
        )

        print(
            f"CKKS logit  : "
            f"{ckks_logits[idx]: .10e}"
        )

        print(
            f"Error       : "
            f"{absolute_errors[idx]: .10e}"
        )

        print(
            f"True label  : "
            f"{plain_labels[idx]}"
        )

        print(
            f"Plain pred  : "
            f"{plain_predictions[idx]}"
        )

        print(
            f"CKKS pred   : "
            f"{ckks_predictions[idx]}"
        )


# ============================================================
# 17. Decision boundary analysis
# ============================================================

print()
print("=" * 60)
print("DECISION BOUNDARY ANALYSIS")
print("=" * 60)


# Distance from decision boundary.
#
# Our classifier uses:
#
#     logit >= 0 -> class 1
#     logit <  0 -> class 0
#
# Therefore samples with small |logit|
# are close to the decision boundary.

margin = np.abs(
    plain_logits
)


closest_indices = np.argsort(
    margin
)[:10]


for idx in closest_indices:

    print()

    print(
        f"Sample {idx}"
    )

    print(
        f"|Plain logit| : "
        f"{margin[idx]:.10e}"
    )

    print(
        f"Plain logit  : "
        f"{plain_logits[idx]: .10e}"
    )

    print(
        f"CKKS logit   : "
        f"{ckks_logits[idx]: .10e}"
    )

    print(
        f"Absolute error: "
        f"{absolute_errors[idx]:.10e}"
    )

    print(
        f"Plain pred   : "
        f"{plain_predictions[idx]}"
    )

    print(
        f"CKKS pred    : "
        f"{ckks_predictions[idx]}"
    )


# ============================================================
# 18. Error percentiles
# ============================================================

print()
print("=" * 60)
print("CKKS ERROR DISTRIBUTION")
print("=" * 60)


for percentile in [50, 75, 90, 95, 99]:

    value = np.percentile(
        absolute_errors,
        percentile
    )

    print(
        f"{percentile:2d}th percentile : "
        f"{value:.10e}"
    )
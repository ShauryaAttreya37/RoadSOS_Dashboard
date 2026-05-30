import numpy as np
import torch
import torch.nn as nn


class RoadSoSPINN(nn.Module):
    def __init__(self, input_dim=7, output_dim=6, hidden_layers=6, hidden_width=128):
        super().__init__()
        layers = [nn.Linear(input_dim, hidden_width), nn.Tanh()]
        for _ in range(hidden_layers - 1):
            layers.extend([nn.Linear(hidden_width, hidden_width), nn.Tanh()])
        layers.append(nn.Linear(hidden_width, output_dim))
        self.net = nn.Sequential(*layers)
        self._init_weights()

    def _init_weights(self):
        for layer in self.net:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def forward(self, x):
        out = self.net(x)
        out = out.clone()
        out[:, 2:3] = torch.sigmoid(out[:, 2:3])
        return out

    def out(self, x):
        y = self.forward(x)
        return {
            "v": y[:, 0:1],
            "theta": y[:, 1:2],
            "mu_eff": y[:, 2:3],
            "x_brain": y[:, 3:4],
            "y_brain": y[:, 4:5],
            "z_brain": y[:, 5:6],
        }


class IMUNormaliser:
    def __init__(self):
        self.mean = None
        self.std = None

    def fit_transform(self, X):
        self.mean = X.mean(axis=0, keepdims=True)
        self.std = X.std(axis=0, keepdims=True) + 1e-8
        return self.transform(X)

    def transform(self, X):
        if self.mean is None or self.std is None:
            raise RuntimeError("IMUNormaliser must be fitted before transform.")
        return (X - self.mean) / self.std

    def inverse_transform(self, X):
        if self.mean is None or self.std is None:
            raise RuntimeError("IMUNormaliser must be fitted before inverse_transform.")
        return X * self.std + self.mean

    @classmethod
    def from_arrays(cls, mean, std):
        obj = cls()
        obj.mean = np.asarray(mean)
        obj.std = np.asarray(std)
        return obj


from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from roadsos_app.modules.losses import pinn_loss
from roadsos_app.modules.pinn_model import IMUNormaliser, RoadSoSPINN


def train(model, X_raw, Y_raw, epochs=3000, lr=1e-3, batch=512, lam=None, save_path="artifacts/roadsos_pinn.pt"):
    norm = IMUNormaliser()
    X = norm.fit_transform(X_raw).astype(np.float32)
    y_mean = np.zeros((1, Y_raw.shape[1]), dtype=np.float32)
    y_std = np.ones((1, Y_raw.shape[1]), dtype=np.float32)
    Y = Y_raw.astype(np.float32)

    loader = DataLoader(TensorDataset(torch.tensor(X), torch.tensor(Y)), batch_size=batch, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))
    history = {"total": [], "data": [], "vehicle": [], "bio": []}

    for _ in range(epochs):
        totals = []
        for xb, yb in loader:
            optimizer.zero_grad(set_to_none=True)
            loss, data, vehicle, bio = pinn_loss(model, xb, yb, lam)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            totals.append((loss.item(), data.item(), vehicle.item(), bio.item()))
        scheduler.step()
        epoch_mean = np.asarray(totals).mean(axis=0)
        for key, value in zip(history, epoch_mean):
            history[key].append(float(value))

    path = Path(save_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": model.state_dict(),
            "norm_mean": norm.mean,
            "norm_std": norm.std,
            "Y_mean": y_mean,
            "Y_std": y_std,
        },
        path,
    )
    return history


def train_default(save_path="artifacts/roadsos_pinn.pt", epochs=25):
    from modules.simulation import build_dataset

    X_raw, Y_raw, _ = build_dataset(n_seeds_each=3)
    return train(RoadSoSPINN(), X_raw, Y_raw, epochs=epochs, save_path=save_path)

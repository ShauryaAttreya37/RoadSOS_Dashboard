from pathlib import Path

import numpy as np
import streamlit as st
import torch

from roadsos_app.modules.injury_metrics import compute_bric, compute_hic15, injury_label, skid_probability
from roadsos_app.modules.pinn_model import IMUNormaliser, RoadSoSPINN


@st.cache_resource
def load_model(path="artifacts/roadsos_pinn.pt"):
    model_path = Path(path)
    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parents[1] / model_path
    if not model_path.exists():
        return None, None, None
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    model = RoadSoSPINN()
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    norm = IMUNormaliser.from_arrays(checkpoint["norm_mean"], checkpoint["norm_std"])
    return model, norm, checkpoint


def run_inference(sim_fn, sim_kwargs, fs=50):
    sim = sim_fn(fs=fs, **sim_kwargs)
    X_raw = np.c_[sim["t"], sim["ax"], sim["ay"], sim["az"], sim["gx"], sim["gy"], sim["gz"]]
    model, norm, checkpoint = load_model()
    if model is None:
        mu_pred = sim["mu"]
    else:
        X = norm.transform(X_raw).astype(np.float32)
        with torch.no_grad():
            outs = model.out(torch.tensor(X))
        y_mean = checkpoint.get("Y_mean", np.zeros((1, 3)))
        y_std = checkpoint.get("Y_std", np.ones((1, 3)))
        mu_pred = (outs["mu_eff"].numpy()[:, 0] * y_std[0, 2]) + y_mean[0, 2]
        mu_pred = np.clip(mu_pred, 0.0, 1.0)

    hic15 = compute_hic15(sim["ax"], sim["ay"], sim["az"], fs)
    bric = compute_bric(sim["gx"], sim["gy"], sim["gz"])
    return {
        **{key: sim[key] for key in ("t", "ax", "ay", "az", "gx", "gy", "gz")},
        "mu_pred": mu_pred,
        "P_skid": skid_probability(mu_pred),
        "hic15": hic15,
        "bric": bric,
        "label": injury_label(hic15, bric),
    }

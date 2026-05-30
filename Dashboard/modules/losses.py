import torch

from modules.injury_metrics import CONSTANTS


def _grad(y, x):
    return torch.autograd.grad(y, x, torch.ones_like(y), create_graph=True, retain_graph=True)[0][:, 0:1]


def residual_vehicle(outs, x):
    dv_dt = _grad(outs["v"], x)
    dtheta_dt = _grad(outs["theta"], x)
    r_v = CONSTANTS["M_TOTAL"] * dv_dt + outs["mu_eff"] * CONSTANTS["M_TOTAL"] * CONSTANTS["G"]
    r_theta = dtheta_dt - outs["v"] * torch.sin(outs["theta"]) / CONSTANTS["WHEELBASE"]
    return r_v, r_theta


def residual_biomechanics(outs, x):
    residuals = []
    for key in ("x_brain", "y_brain", "z_brain"):
        disp = outs[key]
        vel = _grad(disp, x)
        acc = _grad(vel, x)
        residuals.append(
            CONSTANTS["M_BRAIN"] * acc + CONSTANTS["C_BRAIN"] * vel + CONSTANTS["K_BRAIN"] * disp
        )
    return torch.cat(residuals, dim=1)


def pinn_loss(model, x_batch, y_batch, lam=None):
    lam = lam or {"data": 1.0, "vehicle": 0.1, "bio": 0.05}
    x_batch = x_batch.requires_grad_(True)
    outs = model.out(x_batch)
    pred = torch.cat([outs["v"], outs["theta"], outs["mu_eff"]], dim=1)
    data_loss = torch.mean((pred - y_batch) ** 2)
    rv, rt = residual_vehicle(outs, x_batch)
    vehicle_loss = torch.mean(rv**2) + torch.mean(rt**2)
    bio_loss = torch.mean(residual_biomechanics(outs, x_batch) ** 2)
    total = lam["data"] * data_loss + lam["vehicle"] * vehicle_loss + lam["bio"] * bio_loss
    return total, data_loss, vehicle_loss, bio_loss


import numpy as np


CONSTANTS = {
    "HIC_LOW": 700,
    "HIC_HIGH": 1000,
    "BRIC_X": 66.3,
    "BRIC_Y": 56.5,
    "BRIC_Z": 42.2,
    "MU_DRY": 0.75,
    "MU_WET": 0.45,
    "MU_OIL": 0.15,
    "M_TOTAL": 225.0,
    "G": 9.81,
    "WHEELBASE": 1.35,
    "M_BRAIN": 1.4,
    "K_BRAIN": 2.1e4,
    "C_BRAIN": 85.0,
}


def compute_hic15(ax, ay, az, fs, window_ms=15) -> float:
    ar = np.sqrt(ax**2 + ay**2 + az**2) / CONSTANTS["G"]
    dt = 1.0 / fs
    max_window = max(2, int(window_ms * 1e-3 / dt))
    cumulative = np.concatenate([[0.0], np.cumsum(ar)])
    best = 0.0
    for width in range(2, max_window + 1):
        means = (cumulative[width:] - cumulative[:-width]) / width
        values = width * dt * np.maximum(means, 0.0) ** 2.5
        if values.size:
            best = max(best, float(values.max()))
    return best


def compute_bric(gx, gy, gz) -> float:
    return float(
        np.sqrt(
            (np.max(np.abs(gx)) / CONSTANTS["BRIC_X"]) ** 2
            + (np.max(np.abs(gy)) / CONSTANTS["BRIC_Y"]) ** 2
            + (np.max(np.abs(gz)) / CONSTANTS["BRIC_Z"]) ** 2
        )
    )


def injury_label(hic, bric) -> str:
    if hic >= CONSTANTS["HIC_HIGH"] or bric >= 1.0:
        return "SEVERE"
    if hic >= CONSTANTS["HIC_LOW"] or bric >= 0.5:
        return "MODERATE"
    return "LOW"


def skid_probability(mu_eff_array) -> np.ndarray:
    return np.clip((CONSTANTS["MU_WET"] - mu_eff_array) / CONSTANTS["MU_WET"], 0.0, 1.0)


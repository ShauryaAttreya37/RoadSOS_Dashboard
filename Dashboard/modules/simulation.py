import numpy as np

from modules.injury_metrics import CONSTANTS, skid_probability


def simulate_normal(duration=8.0, fs=50, seed=42):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration, int(duration * fs), endpoint=False)
    n = t.size
    v = 11.1 + 0.5 * np.sin(0.3 * t) + 0.1 * rng.normal(size=n)
    theta = 0.05 * np.sin(0.2 * t) + 0.01 * rng.normal(size=n)
    mu = np.clip(CONSTANTS["MU_DRY"] + 0.02 * rng.normal(size=n), 0.6, 0.9)
    return _signals(t, v, theta, mu, fs, rng, scenario=0)


def simulate_oil_patch(duration=8.0, fs=50, seed=43, patch_start=None):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration, int(duration * fs), endpoint=False)
    n = t.size
    pivot = int((patch_start if patch_start is not None else 0.4 * duration) * fs)
    pivot = int(np.clip(pivot, 0, n - 1))
    v = 13.9 + 0.8 * np.sin(0.3 * t)
    mu = np.ones(n) * CONSTANTS["MU_DRY"]
    decay = np.exp(-np.arange(n - pivot) / (0.2 * fs))
    mu[pivot:] = CONSTANTS["MU_OIL"] + (CONSTANTS["MU_DRY"] - CONSTANTS["MU_OIL"]) * decay
    theta = 0.05 * np.sin(0.2 * t)
    theta[pivot:] += 0.3 * (1 - decay)
    return _signals(t, v, theta, np.clip(mu, 0.05, 0.9), fs, rng, scenario=1)


def simulate_crash(duration=2.0, fs=1000, seed=44, crash_time=None):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration, int(duration * fs), endpoint=False)
    n = t.size
    impact = crash_time if crash_time is not None else 0.25 * duration
    ii = int(np.clip(impact * fs, 1, n - 1))
    pre = max(0, ii - int(0.15 * fs))
    v = np.ones(n) * 16.7
    v[pre:ii] = np.linspace(16.7, 10.8, max(ii - pre, 1))
    stop_w = max(1, int(0.05 * fs))
    v[ii : min(ii + stop_w, n)] = np.linspace(10.8, 0.0, min(stop_w, n - ii))
    v[min(ii + stop_w, n) :] = 0.0
    mu = np.ones(n) * CONSTANTS["MU_DRY"]
    mu[pre:ii] = np.linspace(CONSTANTS["MU_DRY"], CONSTANTS["MU_OIL"] + 0.05, max(ii - pre, 1))
    mu[ii:] = CONSTANTS["MU_OIL"]
    theta = np.zeros(n)
    tip_w = max(1, int(0.2 * fs))
    theta[ii : min(ii + tip_w, n)] = np.linspace(0, np.pi / 2, min(tip_w, n - ii))
    theta[min(ii + tip_w, n) :] = np.pi / 2
    data = _signals(t, v, theta, np.clip(mu + 0.01 * rng.normal(size=n), 0.01, 0.9), fs, rng, scenario=2)
    _inject_crash_pulses(data, ii, fs)
    return data


def build_dataset(n_seeds_each=8):
    rows = []
    targets = []
    meta = []
    for seed in range(n_seeds_each):
        for fn in (simulate_normal, simulate_oil_patch, simulate_crash):
            sim = fn(seed=seed)
            x = np.c_[sim["t"], sim["ax"], sim["ay"], sim["az"], sim["gx"], sim["gy"], sim["gz"]]
            y = np.c_[sim["v"], sim["theta"], sim["mu"]]
            rows.append(x)
            targets.append(y)
            meta.append(np.c_[np.full(x.shape[0], sim["scenario"]), sim["t"]])
    return np.vstack(rows), np.vstack(targets), np.vstack(meta)


def _signals(t, v, theta, mu, fs, rng, scenario):
    n = t.size
    ax = np.diff(v, prepend=v[0]) * fs + 0.1 * rng.normal(size=n)
    ay = v * np.gradient(theta, 1 / fs) + 0.1 * rng.normal(size=n)
    az = CONSTANTS["G"] * np.cos(theta) + 0.05 * rng.normal(size=n)
    gx = np.gradient(theta, 1 / fs) + 0.02 * rng.normal(size=n)
    gy = 0.05 * np.sin(0.1 * t) + 0.01 * rng.normal(size=n)
    gz = 0.03 * np.cos(0.15 * t) + 0.01 * rng.normal(size=n)
    return {
        "t": t,
        "ax": ax,
        "ay": ay,
        "az": az,
        "gx": gx,
        "gy": gy,
        "gz": gz,
        "v": v,
        "theta": theta,
        "mu": mu,
        "P_skid": skid_probability(mu),
        "scenario": scenario,
    }


def _inject_crash_pulses(data, impact_index, fs):
    n = data["t"].size
    width = max(1, int(0.025 * fs))
    if impact_index + width < n:
        pulse = 120 * CONSTANTS["G"] * np.sin(np.linspace(0, np.pi, width))
        data["ax"][impact_index : impact_index + width] += pulse
        data["az"][impact_index : impact_index + width] -= 0.25 * pulse
    angular_width = max(1, int(0.03 * fs))
    if impact_index + angular_width < n:
        wave = np.sin(np.linspace(0, np.pi, angular_width))
        data["gx"][impact_index : impact_index + angular_width] += 78 * wave
        data["gy"][impact_index : impact_index + angular_width] += 62 * wave
        data["gz"][impact_index : impact_index + angular_width] += 48 * wave


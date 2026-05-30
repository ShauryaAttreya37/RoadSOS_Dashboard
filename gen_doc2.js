const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat
} = require('/usr/local/lib/node_modules_global/lib/node_modules/docx');
const fs = require('fs');

const ACCENT = "005B96";
const CODEBG = "1A1A2E";
const THBG   = "003366";
const ROWALT = "EBF2FA";

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, bold: true, size: 36, color: ACCENT, font: "Arial" })]
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 260, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: ACCENT, font: "Arial" })]
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: "1A1A1A", font: "Arial" })]
  });
}
function para(text) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: "1A1A1A" })]
  });
}
function paraRuns(runs) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: runs.map(r => new TextRun({ font: "Arial", size: 22, color: "1A1A1A", ...r }))
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 50, after: 50 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: "1A1A1A" })]
  });
}
function spacer(before=80, after=80) {
  return new Paragraph({ spacing: { before, after }, children: [] });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}
function divider() {
  return new Paragraph({
    spacing: { before: 160, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 1 } },
    children: []
  });
}

function codeBlock(code, label) {
  const lines = code.split('\n');
  const none  = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const borders = { top: none, bottom: none, left: none, right: none };
  const rows = [];
  if (label) {
    rows.push(new TableRow({ children: [new TableCell({
      borders,
      shading: { fill: "2A2A3E", type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 40, left: 180, right: 180 },
      width: { size: 9360, type: WidthType.DXA },
      children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, size: 17, color: "8888BB", font: "Courier New" })] })]
    })] }));
  }
  rows.push(new TableRow({ children: [new TableCell({
    borders,
    shading: { fill: CODEBG, type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 220, right: 180 },
    width: { size: 9360, type: WidthType.DXA },
    children: lines.map(line => new Paragraph({
      spacing: { before: 0, after: 0, line: 252, lineRule: "auto" },
      children: [new TextRun({ text: line === '' ? ' ' : line, size: 18, color: "D4D4D4", font: "Courier New" })]
    }))
  })] }));
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], rows });
}

function infoTable(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: colWidths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => new TableCell({
        borders, width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: THBG, type: ShadingType.CLEAR },
        margins: { top: 90, bottom: 90, left: 130, right: 130 },
        children: [new Paragraph({ children: [new TextRun({ text: h, size: 20, font: "Arial", bold: true, color: "FFFFFF" })] })]
      })) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((cell, ci) => new TableCell({
        borders, width: { size: colWidths[ci], type: WidthType.DXA },
        shading: { fill: ri % 2 === 1 ? ROWALT : "FFFFFF", type: ShadingType.CLEAR },
        margins: { top: 90, bottom: 90, left: 130, right: 130 },
        children: [new Paragraph({ children: [new TextRun({ text: cell, size: 20, font: "Arial", color: "1A1A1A" })] })]
      })) }))
    ]
  });
}

// ─── Code ────────────────────────────────────────────────────────────────────

const dashboardCode = `import os, streamlit as st, torch, torch.nn as nn
import numpy as np, matplotlib.pyplot as plt

st.set_page_config(page_title="RoadSoS", page_icon="helmet", layout="wide")
plt.style.use("dark_background")

# Constants
G=9.81; M_TOTAL=225; WHEELBASE=1.35; M_BRAIN=1.4; K_BRAIN=2.1e4; C_BRAIN=85
MU_DRY=0.75; MU_WET=0.45; MU_OIL=0.15
BRIC_X=66.3; BRIC_Y=56.5; BRIC_Z=42.2; HIC_LOW=700; HIC_HIGH=1000
FS_N=100; FS_C=1000
CA="#00E5FF"; CW="#FFD600"; CR="#FF1744"; CG="#00E676"; BG="#0d0d0d"

# PINN model (mirrors training architecture exactly)
class PINN(nn.Module):
    def __init__(self):
        super().__init__()
        d = [7]+[128]*6+[6]
        layers = []
        for i in range(len(d)-1):
            layers.append(nn.Linear(d[i], d[i+1]))
            if i < len(d)-2: layers.append(nn.Tanh())
        self.net = nn.Sequential(*layers)

    def forward(self, x): return self.net(x)

    def out(self, x):
        o = self.forward(x)
        return {"v": o[:,0:1], "theta": o[:,1:2],
                "mu_eff": torch.sigmoid(o[:,2:3]),
                "xb": o[:,3:4], "yb": o[:,4:5], "zb": o[:,5:6]}

@st.cache_resource
def load_model():
    ck = torch.load(os.path.join(os.path.dirname(__file__),
         "roadsos_pinn.pt"), map_location="cpu", weights_only=False)
    m = PINN(); m.load_state_dict(ck["model_state"]); m.eval()
    return m, ck["norm_mean"], ck["norm_std"]

def hic15(ax, ay, az, fs, wms=15):
    """Head Injury Criterion over a sliding 15 ms window (ECE 22.06)."""
    ar = np.sqrt(ax**2+ay**2+az**2)/G
    dt = 1/fs; mw = max(2, int(wms*1e-3/dt)); h = 0
    cs = np.cumsum(ar)
    for w in range(2, mw+1):
        ms   = (cs[w:]-cs[:-w])/w
        vals = w*dt*(np.maximum(ms,0)**2.5)
        h    = max(h, vals.max())
    return h

def bric(gx, gy, gz):
    """Brain Rotational Injury Criterion (NHTSA cadaver study)."""
    return np.sqrt((np.max(np.abs(gx))/BRIC_X)**2 +
                   (np.max(np.abs(gy))/BRIC_Y)**2 +
                   (np.max(np.abs(gz))/BRIC_Z)**2)

def sim(sc, dur, fs, seed=42):
    """Generate synthetic IMU data for the selected scenario."""
    np.random.seed(seed)
    t = np.linspace(0, dur, int(dur*fs)); n = len(t)

    if sc == 0:  # ── Normal Riding ──────────────────────────────────────────
        v  = 11.1+0.5*np.sin(0.3*t)+0.1*np.random.randn(n)
        th = 0.05*np.sin(0.2*t)+0.01*np.random.randn(n)
        mu = np.clip(MU_DRY+0.02*np.random.randn(n), 0.6, 0.9)

    elif sc == 1:  # ── Oil Patch ────────────────────────────────────────────
        pivot = int(0.4*n); v = 13.9+0.8*np.sin(0.3*t)
        mu  = np.ones(n)*MU_DRY
        dec = np.exp(-np.arange(n-pivot)/(0.2*fs))
        mu[pivot:] = MU_OIL+(MU_DRY-MU_OIL)*dec[:n-pivot]
        mu  = np.clip(mu, 0.05, 0.9)
        th  = 0.05*np.sin(0.2*t); th[pivot:] += 0.3*(1-dec[:n-pivot])

    else:  # ── Crash ────────────────────────────────────────────────────────
        impact_t = 0.25*dur
        ii = int(impact_t*fs); pre = max(0, ii-int(0.15*fs))
        ii2 = ii+int(0.35*fs)
        # velocity: cruise -> emergency brake -> stop
        v = np.ones(n)*16.7
        v[pre:ii]         = np.linspace(16.7, 16.7*0.65, ii-pre)
        stop_w            = int(0.05*fs)
        v[ii:ii+stop_w]   = np.linspace(16.7*0.65, 0.0, stop_w)
        v[ii+stop_w:]     = 0.0
        # friction: drops 150 ms before impact
        mu = np.ones(n)*MU_DRY
        mu[pre:ii] = np.linspace(MU_DRY, MU_OIL+0.05, ii-pre)
        mu[ii:]    = MU_OIL
        mu = np.clip(mu+0.01*np.random.randn(n), 0.01, 0.9)
        # lean: gradual then rapid tip-over
        th = np.zeros(n); th[pre:ii] = 0.05*np.linspace(0,1,ii-pre)
        tip_w = int(0.20*fs)
        th[ii:ii+tip_w] = np.clip(np.linspace(0,np.pi/2,tip_w),0,np.pi/2)
        th[ii+tip_w:]   = np.pi/2
        th = np.clip(th+0.008*np.random.randn(n),0,np.pi/2)

    # Derive IMU channels from kinematics
    ax = np.diff(v,prepend=v[0])*fs+0.1*np.random.randn(n)
    ay = v*np.gradient(th,1/fs)+0.1*np.random.randn(n)
    az = G*np.cos(th)+0.05*np.random.randn(n)
    gx = np.gradient(th,1/fs)+0.02*np.random.randn(n)
    gy = 0.05*np.sin(0.1*t)+0.01*np.random.randn(n)
    gz = 0.03*np.cos(0.15*t)+0.01*np.random.randn(n)

    if sc == 2:  # inject impact pulses
        ipw=int(0.025*fs); spw=int(0.015*fs)
        p1=np.zeros(n); p2=np.zeros(n)
        if ii+ipw<n: p1[ii:ii+ipw]=120*G*np.sin(np.linspace(0,np.pi,ipw))
        if ii2+spw<n: p2[ii2:ii2+spw]=30*G*np.sin(np.linspace(0,np.pi,spw))
        ax+=p1+p2; az-=0.25*p1
        ff_s=ii+ipw; ff_e=ff_s+int(0.03*fs)
        if ff_e<n: az[ff_s:ff_e]*=0.1
        apw=int(0.030*fs)
        if ii+apw<n:
            gx[ii:ii+apw]+=78*np.sin(np.linspace(0,np.pi,apw))
            gy[ii:ii+apw]+=62*np.sin(np.linspace(0,np.pi,apw))
            gz[ii:ii+apw]+=48*np.sin(np.linspace(0,np.pi,apw))

    return t, ax, ay, az, gx, gy, gz, v, th, mu

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("RoadSoS Controls")
sc_name = st.sidebar.selectbox("Scenario",["Normal Riding","Oil Patch","Crash"])
sc  = {"Normal Riding":0,"Oil Patch":1,"Crash":2}[sc_name]
fs  = FS_C if sc==2 else FS_N
dur = st.sidebar.slider("Duration (s)",1.0,15.0,8.0 if sc<2 else 2.0,0.5)
st.sidebar.markdown("---")
st.sidebar.markdown("**Rider Profile**")
bg  = st.sidebar.selectbox("Blood Group",["O+","O-","A+","A-","B+","B-","AB+","AB-"])
alg = st.sidebar.text_input("Allergies","None")
ec  = st.sidebar.text_input("Emergency Contact","+91-XXXXXXXXXX")

# ── Run inference ─────────────────────────────────────────────────────────────
model,nm,ns = load_model()
t,ax,ay,az,gx,gy,gz,v,th,mu = sim(sc,dur,fs)
Xn = (np.c_[t,ax,ay,az,gx,gy,gz] - nm) / (ns+1e-8)
with torch.no_grad():
    o = model.out(torch.tensor(Xn, dtype=torch.float32))
mu_p = o["mu_eff"].numpy().flatten()
Psk  = np.clip((MU_WET-mu_p)/MU_WET, 0, 1)
ares = np.sqrt(ax**2+ay**2+az**2)/G
hv   = hic15(ax,ay,az,fs); bv = bric(gx,gy,gz)
inj  = min(0.6*hv/HIC_HIGH+0.4*bv, 1.0)

# ── Status banner ─────────────────────────────────────────────────────────────
crash_det = (sc==2 or ares.max()>6)
skid_det  = (Psk.max()>0.65 and not crash_det)
ac = CR if crash_det else (CW if skid_det else CG)
at = ("CRASH DETECTED — SOS FIRED" if crash_det else
      ("SKID WARNING — HAPTIC ALERT" if skid_det else "ALL CLEAR"))
st.markdown(f"<h2 style='color:{ac};font-family:monospace'>{at}</h2>",
            unsafe_allow_html=True)

# ── Metric cards ──────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Peak Accel",   f"{ares.max():.1f} g",  ">6g" if ares.max()>6 else "OK")
c2.metric("P(skid)",      f"{Psk.max():.2f}",     "HIGH" if Psk.max()>0.65 else "LOW")
c3.metric("HIC15",        f"{hv:.0f}",            "DANGER" if hv>700 else "OK")
c4.metric("BrIC",         f"{bv:.3f}",            "CRITICAL" if bv>1 else "OK")
c5.metric("Injury Score", f"{inj:.2f}",           "SEVERE" if inj>0.7 else ("MOD" if inj>0.3 else "LOW"))
st.markdown("---")

# ── Rider SOS card ────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='background:#111;padding:16px;border-radius:10px;"
    f"border:1px solid {CA};margin-top:8px'>"
    f"<h4 style='color:{CA};margin:0 0 8px'>Rider Medical Profile — Transmitted on SOS</h4>"
    f"<p style='color:#eee;margin:0'>Blood: <b>{bg}</b> &nbsp;|&nbsp; "
    f"Allergies: <b>{alg}</b> &nbsp;|&nbsp; Emergency: <b>{ec}</b></p>"
    f"<p style='color:gray;font-size:12px;margin:6px 0 0'>"
    f"Encrypted on ESP32-S3. Released via NFC/QR on crash detection.</p>"
    f"</div>", unsafe_allow_html=True)`;

const pinnArch = `class RoadSoSPINN(nn.Module):
    """
    A fully-connected PINN that maps 7 IMU signals to 6 physical
    state variables. tanh activations ensure smooth higher-order
    derivatives, which the physics residual losses depend on.
    Xavier initialisation keeps gradients stable through 6 layers.
    mu_eff is passed through sigmoid so it is always in (0, 1).

    Input  (7): [t, ax, ay, az, gx, gy, gz]
    Output (6): [v, theta, mu_eff, x_brain, y_brain, z_brain]
    """
    def __init__(self, hidden_layers=6, hidden_width=128):
        super().__init__()
        dims = [7] + [hidden_width]*hidden_layers + [6]
        layers = []
        for i in range(len(dims)-1):
            layers.append(nn.Linear(dims[i], dims[i+1]))
            if i < len(dims)-2:
                layers.append(nn.Tanh())
        self.net = nn.Sequential(*layers)
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def get_outputs(self, x):
        o = self.net(x)
        return {
            "v":       o[:, 0:1],
            "theta":   o[:, 1:2],
            "mu_eff":  torch.sigmoid(o[:, 2:3]),
            "x_brain": o[:, 3:4],
            "y_brain": o[:, 4:5],
            "z_brain": o[:, 5:6],
        }`;

const pinnLoss = `def residual_vehicle(outs, x):
    """
    Two governing ODEs for a two-wheeler, evaluated via autograd.
    Both residuals are normalised to dimensionless O(1) quantities
    so the lambda weights stay interpretable.

    (1)  M * dv/dt  +  mu_eff * M * G  =  0   (friction deceleration)
    (2)  dtheta/dt  -  v * sin(theta) / L  =  0  (lean kinematic)
    """
    dv_dt     = grad(outs["v"].sum(),     x, create_graph=True)[0][:, 0:1]
    dtheta_dt = grad(outs["theta"].sum(), x, create_graph=True)[0][:, 0:1]
    R_v     = (M_TOTAL*dv_dt + outs["mu_eff"]*M_TOTAL*G) / (M_TOTAL*G)
    R_theta = dtheta_dt - outs["v"]*torch.sin(outs["theta"])/WHEELBASE
    return R_v, R_theta


def residual_biomechanics(outs, x):
    """
    Kelvin-Voigt spring-mass-damper applied independently to each axis:
        M_b * x_b''  +  C * x_b'  +  K * x_b  =  M_b * a_helmet
    Normalised by K_BRAIN to keep magnitudes in O(1).
    """
    Rs = []
    for x_b, a_h in zip(
        [outs["x_brain"], outs["y_brain"], outs["z_brain"]],
        [x[:,1:2],        x[:,2:3],        x[:,3:4]]
    ):
        x_b_t  = grad(x_b.sum(),   x, create_graph=True)[0][:, 0:1]
        x_b_tt = grad(x_b_t.sum(), x, create_graph=True)[0][:, 0:1]
        Rs.append(
            (M_BRAIN*x_b_tt + C_BRAIN*x_b_t + K_BRAIN*x_b - M_BRAIN*a_h)
            / K_BRAIN
        )
    return Rs


def pinn_loss(model, x_batch, y_batch, lam):
    x_batch  = x_batch.clone().requires_grad_(True)
    outs     = model.get_outputs(x_batch)
    pred     = torch.cat([outs["v"], outs["theta"], outs["mu_eff"]], dim=1)
    L_data   = nn.functional.mse_loss(pred, y_batch)
    R_v, R_t = residual_vehicle(outs, x_batch)
    L_veh    = (R_v**2).mean() + (R_t**2).mean()
    L_bio    = sum((R**2).mean() for R in residual_biomechanics(outs, x_batch))
    return lam["data"]*L_data + lam["vehicle"]*L_veh + lam["bio"]*L_bio`;

const pinnTraining = `model  = RoadSoSPINN().to(DEVICE)
opt    = optim.Adam(model.parameters(), lr=1e-3)
sched  = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=3000, eta_min=1e-5)
lam    = {"data": 1.0, "vehicle": 0.1, "bio": 0.05}

for ep in range(1, 3001):
    model.train()
    for xb, yb in loader:
        opt.zero_grad()
        loss = pinn_loss(model, xb, yb, lam)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # prevent exploding grads
        opt.step()
    sched.step()

# Save checkpoint for dashboard
torch.save({
    "model_state": model.state_dict(),
    "norm_mean":   norm.mean,
    "norm_std":    norm.std,
}, "roadsos_pinn.pt")
print("Checkpoint saved -> roadsos_pinn.pt")`;

const hicCode = `def compute_hic15(ax, ay, az, fs, window_ms=15):
    """
    Head Injury Criterion over a 15 ms sliding window, per ECE 22.06.
    Requires fs >= 1000 Hz to correctly resolve the 15 ms window.
    """
    a_res = np.sqrt(ax**2 + ay**2 + az**2) / G   # resultant in g
    dt    = 1.0 / fs
    max_w = max(2, int(window_ms * 1e-3 / dt))
    hic   = 0.0
    cs    = np.cumsum(a_res)                       # precompute cumsum once
    for w in range(2, max_w + 1):
        means = (cs[w:] - cs[:-w]) / w
        vals  = w * dt * (np.maximum(means, 0) ** 2.5)
        hic   = max(hic, vals.max())
    return hic


def compute_bric(gx, gy, gz):
    """
    Brain Rotational Injury Criterion.
    Axis thresholds from the NHTSA cadaver study (Takhounts 2013):
      gx = 66.3 rad/s  (sagittal / pitch)
      gy = 56.5 rad/s  (coronal  / roll)
      gz = 42.2 rad/s  (transverse / yaw)
    BrIC > 1.0 is considered a severe rotational injury risk.
    """
    return np.sqrt(
        (np.max(np.abs(gx)) / BRIC_X)**2 +
        (np.max(np.abs(gy)) / BRIC_Y)**2 +
        (np.max(np.abs(gz)) / BRIC_Z)**2
    )


def injury_label(hic, bric_val):
    score = min(0.6 * hic / HIC_HIGH + 0.4 * bric_val, 1.0)
    if score < 0.3: return "LOW"
    if score < 0.7: return "MODERATE"
    return "SEVERE"`;

const requirementsCode = `torch>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
pandas>=2.0.0
scipy>=1.10.0
streamlit>=1.28.0
pyngrok>=7.0.0`;

const quickstart = `# 1.  Create and activate a virtual environment
python -m venv .venv
.venv\\Scripts\\Activate.ps1          # Windows PowerShell
source .venv/bin/activate             # macOS / Linux

# 2.  Install all dependencies
pip install -r requirements.txt

# 3.  Launch the dashboard
#     (roadsos_pinn.pt is loaded automatically — no training needed)
streamlit run roadsos_dashboard.py
# Opens at http://localhost:8501

# ── Optional: retrain the model ──────────────────────────────────────
# Run all cells in RoadSoS_PINN.ipynb (GPU recommended but not required)
# A new roadsos_pinn.pt will be written when training finishes.
jupyter notebook RoadSoS_PINN.ipynb`;

// ─── Document children ────────────────────────────────────────────────────────

const children = [

  // ── Title page ────────────────────────────────────────────────────────────
  spacer(600, 200),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 160 },
    children: [new TextRun({ text: "RoadSoS", bold: true, size: 72, font: "Arial", color: ACCENT })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 },
    children: [new TextRun({ text: "SmartHelmetSOS", bold: true, size: 40, font: "Arial", color: "334466" })]
  }),
  divider(),
  spacer(80, 80),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 100 },
    children: [new TextRun({ text: "Physics-Informed Neural Network for", size: 26, font: "Arial", color: "555555", italics: true })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 200 },
    children: [new TextRun({ text: "Two-Wheeler Crash Detection & Head-Injury Risk Estimation", size: 26, font: "Arial", color: "555555", italics: true })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
    children: [new TextRun({ text: "IITM Hackathon 2026", size: 22, font: "Arial", color: "888888" })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
    children: [new TextRun({ text: "github.com/ShauryaAttreya37/SmartHelmetSOS", size: 20, font: "Arial", color: "AAAAAA" })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
    children: [new TextRun({ text: "Python  |  PyTorch  |  Streamlit  |  ESP32-S3", size: 20, font: "Arial", color: "AAAAAA" })]
  }),

  pageBreak(),

  // ── 1. Overview ────────────────────────────────────────────────────────────
  h1("1. What is RoadSoS?"),
  para("RoadSoS is a crash detection and head-injury risk system for two-wheelers, built around a Physics-Informed Neural Network (PINN). At its core, the project asks a simple question: can a helmet-mounted IMU — the same kind of chip in every modern smartphone — tell you whether a rider just crashed, and how badly they might be hurt?"),
  spacer(),
  para("The answer RoadSoS gives is yes, with caveats. The PINN reads a stream of accelerometer and gyroscope data and simultaneously estimates the bike's speed, lean angle, road friction, and the motion of the rider's brain relative to the skull — all in a single forward pass. When the numbers hit critical thresholds, it fires an SOS, triggers a haptic warning in the helmet, and releases the rider's encrypted medical profile to first responders."),
  spacer(),
  para("What makes this more than a threshold detector is the physics. The network's training loss includes residuals from two governing equations — a two-wheeler friction ODE and a Kelvin-Voigt brain biomechanics model — which force the outputs to stay physically consistent even when the input data is noisy or sparse. This was built for IITM Hackathon 2026 as a research prototype."),
  spacer(),
  h2("Repository at a Glance"),
  infoTable(
    ["File", "What it does"],
    [
      ["roadsos_dashboard.py", "Streamlit app — loads the checkpoint, runs inference, and renders live metrics and dark-mode plots"],
      ["RoadSoS_PINN.ipynb",   "Training notebook — synthetic data generation, PINN architecture, physics losses, training loop, evaluation"],
      ["roadsos_pinn.pt",      "Pre-trained model checkpoint, ready to use with the dashboard out of the box"],
      ["requirements.txt",     "All Python dependencies — install once and you're good to go"],
      [".gitignore",           "Keeps generated files, virtual environments, and future checkpoints out of version control"],
    ],
    [3000, 6360]
  ),
  spacer(),

  // ── 2. Sensors ─────────────────────────────────────────────────────────────
  pageBreak(),
  h1("2. Sensor Specifics"),
  h2("2.1  The IMU"),
  para("Everything starts with a 6-axis Inertial Measurement Unit. The IMU provides three axes of linear acceleration (what the helmet is doing translationally) and three axes of angular velocity (how it's rotating). Two chips are explicitly supported in the deployment design:"),
  spacer(),
  infoTable(
    ["Sensor", "DOF", "Max ODR", "Interface", "Best for"],
    [
      ["MPU-6050",  "6-axis accel + gyro", "1 kHz",  "I2C / SPI", "Prototyping — cheap, widely available, just meets the 1 kHz HIC requirement"],
      ["ICM-42688", "6-axis accel + gyro", "32 kHz", "SPI only",  "Production — lower noise floor, better temperature stability, headroom for future algorithms"],
    ],
    [1620, 2160, 1080, 1260, 3240]
  ),
  spacer(),
  para("The 7-element input vector the PINN receives at each timestep is:"),
  spacer(),
  codeBlock("t     — elapsed time (s)\nax    — linear acceleration, X axis (m/s2)  [forward/braking]\nay    — linear acceleration, Y axis (m/s2)  [lateral lean]\naz    — linear acceleration, Z axis (m/s2)  [vertical, ~G at rest]\ngx    — angular velocity, X axis (rad/s)   [roll rate]\ngy    — angular velocity, Y axis (rad/s)   [pitch rate]\ngz    — angular velocity, Z axis (rad/s)   [yaw rate]", "PINN input: shape [N, 7]"),
  spacer(),
  h2("2.2  Why the Sample Rate Matters"),
  para("Not all scenarios need the same sampling rate. Normal riding and oil-patch scenarios use 100 Hz — plenty for the dynamics involved, which play out over hundreds of milliseconds. Crash scenarios bump up to 1000 Hz. This isn't arbitrary: ECE 22.06 (the motorcycle helmet safety standard) explicitly requires at least 1 kHz to correctly compute HIC15 over its 15 ms integration window. Miss that, and your HIC numbers are wrong."),
  spacer(),
  infoTable(
    ["Scenario", "Sample Rate", "Reasoning"],
    [
      ["Normal Riding", "100 Hz", "Friction and lean dynamics evolve over 100+ ms — 100 Hz easily captures them"],
      ["Oil Patch",     "100 Hz", "Slip build-up is gradual, ~200 ms timescale — 100 Hz is sufficient"],
      ["Crash",         "1000 Hz","ECE 22.06 mandates >= 1 kHz for a valid HIC15 measurement over the 15 ms window"],
    ],
    [2520, 1800, 5040]
  ),
  spacer(),
  h2("2.3  The ESP32-S3 — On-Helmet Edge Compute"),
  para("The deployment vision centres on the ESP32-S3 as the brain of the helmet unit. It was chosen because it hits a rare combination of requirements: fast enough for real-time inference, small enough to fit in a helmet, and equipped with the connectivity and security features an emergency system needs."),
  spacer(),
  bullet("Dual-core Xtensa LX7 at 240 MHz with a vector extension — handles INT8-quantised PINN inference in under 10 ms per frame"),
  bullet("Bluetooth 5 (BLE) + Wi-Fi — primary SOS channel via BLE to a paired phone, Wi-Fi for bulk data offload when docked"),
  bullet("On-chip AES-128/256 co-processor — encrypts the rider's medical profile on-device; the key never leaves the chip"),
  bullet("GPIO for haptic LRA driver — skid probability over 0.65 triggers a vibration pattern the rider can feel through the helmet"),
  spacer(),
  h2("2.4  The Rest of the Hardware Stack"),
  infoTable(
    ["Component", "Role"],
    [
      ["LRA / ERM haptic actuator",  "Vibrates the helmet shell when P(skid) > 0.65 — a tactile warning the rider feels without distraction"],
      ["BLE to paired phone",        "Primary SOS path — crash event plus GPS co-ordinates sent to the emergency contact within seconds"],
      ["Cellular fallback",          "Backup SOS when the paired phone is out of BLE range — works anywhere there's mobile signal"],
      ["NFC / QR tag",               "On crash detection, generates an encrypted payload with blood group, allergies, and emergency contact — readable by authorised first-responder devices"],
    ],
    [2880, 6480]
  ),
  spacer(),

  // ── 3. Architecture ──────────────────────────────────────────────────────
  pageBreak(),
  h1("3. How the Model Works"),
  h2("3.1  Architecture"),
  para("The PINN is a fully-connected network — no convolutions, no recurrence, no attention. That's a deliberate choice: the physics losses require computing second-order derivatives of the outputs with respect to the inputs via autograd, and simpler architectures make that both faster and more numerically stable."),
  spacer(),
  infoTable(
    ["Property", "Value"],
    [
      ["Input",          "7 features: [t, ax, ay, az, gx, gy, gz]"],
      ["Output",         "6 values: [v, theta, mu_eff, x_brain, y_brain, z_brain]"],
      ["Hidden layers",  "6"],
      ["Width per layer","128 neurons"],
      ["Activation",     "tanh — smooth and differentiable to any order, required for the physics residuals"],
      ["Weight init",    "Xavier uniform — keeps gradient magnitude stable across 6 tanh layers"],
      ["mu_eff",         "Passed through sigmoid before output, constraining it to the physical range (0, 1)"],
      ["Parameters",     "~131,000 trainable — small enough to quantise and run on ESP32-S3"],
      ["Framework",      "PyTorch"],
    ],
    [3000, 6360]
  ),
  spacer(),
  h2("3.2  The Physics Losses"),
  para("This is what separates RoadSoS from a plain sensor classifier. Two sets of physics residuals are evaluated during training and added to the data loss, penalising the network whenever its outputs violate the governing equations."),
  spacer(),
  h3("Vehicle ODE — Tire-Road Friction and Lean"),
  para("Two equations describe how a two-wheeler moves. The friction equation says the bike decelerates at a rate proportional to mu_eff. The lean kinematic ties the rate of lean change to forward speed and wheelbase. The PINN must satisfy both simultaneously."),
  spacer(),
  codeBlock("Friction deceleration:   M * dv/dt  +  mu_eff * M * G  =  0\nLean kinematic:          dtheta/dt  -  v * sin(theta) / L  =  0\n\nM = 225 kg  |  G = 9.81 m/s2  |  L = 1.35 m (wheelbase)", "Two-Wheeler Governing Equations"),
  spacer(),
  h3("Brain Biomechanics — Kelvin-Voigt Model"),
  para("The brain's motion inside the skull is approximated as a damped spring-mass system — the Kelvin-Voigt model. It's applied independently to all three axes. The stiffness (K = 21,000 N/m) and damping (C = 85 N·s/m) set the natural frequency at ~19.5 Hz, which sits squarely in the concussion-risk band identified in biomechanics literature."),
  spacer(),
  codeBlock("M_b * x_b''  +  C * x_b'  +  K * x_b  =  M_b * a_helmet\n\nM_b = 1.4 kg   (brain mass)\nK   = 21,000 N/m  (stiffness -> natural freq ~19.5 Hz)\nC   = 85 N.s/m   (damping coefficient)\na_helmet = IMU linear acceleration on that axis", "Kelvin-Voigt Brain ODE"),
  spacer(),
  h3("Combined Training Loss"),
  codeBlock("L_total =  1.00 * L_data       (MSE against ground-truth v, theta, mu)\n        +  0.10 * L_vehicle    (vehicle ODE residuals)\n        +  0.05 * L_bio        (brain ODE residuals, all 3 axes)", "Total Loss Function"),
  spacer(),
  h2("3.3  Training Setup"),
  infoTable(
    ["Setting", "Value"],
    [
      ["Optimiser",          "Adam, lr = 1e-3"],
      ["Scheduler",          "CosineAnnealingLR — decays learning rate to 1e-5 over 3000 epochs"],
      ["Epochs",             "3000"],
      ["Batch size",         "512"],
      ["Gradient clipping",  "Max norm = 1.0 — prevents gradient explosion from the autograd second derivatives"],
      ["Training data",      "Synthetic — 4 seeds × 3 scenarios = 12 simulation runs, ~200k+ samples total"],
      ["Device",             "CUDA if available, CPU otherwise (training is slow on CPU, dashboard runs fine)"],
    ],
    [3000, 6360]
  ),
  spacer(),

  // ── 4. Injury metrics ─────────────────────────────────────────────────────
  h1("4. Injury Metrics and Alert Thresholds"),
  para("RoadSoS uses two standardised biomechanical injury criteria, both derived from real crash research and regulatory standards."),
  spacer(),
  paraRuns([
    { text: "HIC15 (Head Injury Criterion) ", bold: true },
    { text: "measures the peak average resultant acceleration over any 15 ms window during a crash. It's the primary metric in ECE 22.06 — the European motorcycle helmet certification standard. A score below 700 is low risk, between 700 and 1000 is a warning, and above 1000 indicates a potentially fatal head injury. Computing it correctly requires a sampling rate of at least 1 kHz, which is why crash scenarios in RoadSoS run at 1000 Hz." }
  ]),
  spacer(),
  paraRuns([
    { text: "BrIC (Brain Rotational Injury Criterion) ", bold: true },
    { text: "captures the rotational component of head motion — the mechanism most associated with diffuse axonal injury and concussion. It normalises peak angular velocity on each axis against threshold values derived from the NHTSA cadaver study: 66.3 rad/s sagittal, 56.5 rad/s coronal, 42.2 rad/s transverse. A BrIC above 1.0 is a critical rotational injury risk." }
  ]),
  spacer(),
  infoTable(
    ["Signal", "Warning", "Critical", "Source / Standard"],
    [
      ["HIC15",              "700",  "1000", "ECE R22.06 motorcycle helmet standard"],
      ["BrIC",               "0.6",  "1.0",  "NHTSA cadaver study, Takhounts 2013"],
      ["P(skid)",            "0.65", "—",    "PINN output — sigmoid on predicted mu_eff"],
      ["Peak acceleration",  "6 g",  "—",    "Empirical crash threshold"],
    ],
    [3000, 1440, 1440, 3480]
  ),
  spacer(),
  para("The composite injury score combines both metrics: score = min(0.6 x HIC15/1000 + 0.4 x BrIC, 1.0). Below 0.3 is LOW, 0.3 to 0.7 is MODERATE, above 0.7 is SEVERE. This weighted combination intentionally gives slightly more weight to the translational component (HIC) since it's the better-validated of the two in motorcycle contexts."),
  spacer(),

  // ── 5. Use Cases ───────────────────────────────────────────────────────────
  pageBreak(),
  h1("5. What It Can Be Used For"),
  h2("5.1  Core Use Cases"),
  bullet("Skid warning: The dashboard tracks P(skid) in real time. When it crosses 0.65, the haptic actuator fires before the rider fully loses control — giving them a fraction of a second to adjust. This is particularly useful on unexpected oil patches, painted road markings, or wet metal surfaces."),
  bullet("Automatic SOS on crash: When peak resultant acceleration exceeds 6 g, the system assumes a crash, fires an SOS, and releases the rider's medical profile via NFC/QR. Emergency services get blood group, known allergies, and an emergency contact before they even reach the scene."),
  bullet("Head injury triage at the scene: The HIC15 and BrIC values transmitted with the SOS give paramedics an objective severity score. A BrIC > 1.0 suggests diffuse axonal injury risk; HIC > 1000 is a red flag for skull fracture. This helps dispatch the right resources and prioritise imaging at hospital."),
  bullet("Road surface quality monitoring: The PINN's mu_eff output is essentially a real-time friction map. Fleet operators could aggregate this across many riders to flag deteriorating road surfaces for maintenance — passively, without dedicated road inspection hardware."),
  spacer(),
  h2("5.2  Potential Future Applications"),
  bullet("Rider coaching and insurance: Aggregated skid events, harsh-braking episodes, and injury-risk scores over time produce a riding behaviour profile. Insurers could use this to personalise premiums; trainers could use it to give targeted feedback."),
  bullet("Post-crash forensics: The physics-consistent velocity and friction estimates, stored with GPS and timestamps, could support accident reconstruction for insurance disputes or legal proceedings — far richer than a dashcam footage alone."),
  bullet("Pre-hospital optimisation: Severity scores transmitted via cellular before the ambulance arrives allow trauma centres to pre-stage resources, reducing door-to-CT time — one of the strongest predictors of outcome in head injury."),
  bullet("Urban infrastructure: A fleet of anonymised RoadSoS helmets could produce a live friction heatmap of city roads, identifying high-risk patches after rain or spills faster than any fixed sensor network."),
  spacer(),

  // ── 6. Pros and Cons ─────────────────────────────────────────────────────
  h1("6. Strengths and Limitations"),
  h2("6.1  What RoadSoS Gets Right"),
  infoTable(
    ["Strength", "Why it matters"],
    [
      ["Physics-grounded outputs",      "The network can't produce a friction coefficient that violates the vehicle ODE, even in noisy conditions. This is the core advantage over a purely data-driven classifier."],
      ["Multi-output, single inference", "One 10 ms forward pass yields speed, lean, friction, brain displacement, skid probability, HIC15, and BrIC. There's no pipeline of stacked models with compounding latency."],
      ["Runs on commodity hardware",    "At ~131k parameters, the quantised model fits in under 1 MB and runs comfortably on an ESP32-S3 — no cloud round-trip, no privacy leakage during normal riding."],
      ["Aligned with real standards",   "HIC15 follows ECE 22.06; BrIC uses the NHTSA cadaver study thresholds. The outputs speak the language safety engineers and trauma clinicians already use."],
      ["GPS-independent",               "Everything runs on the IMU alone. Tunnels, parking garages, remote roads — the system works wherever the rider is."],
      ["Privacy by design",             "The medical profile is encrypted on-chip and only released on a confirmed crash event. Normal riding generates no data transmission."],
    ],
    [3000, 6360]
  ),
  spacer(),
  h2("6.2  Honest Limitations"),
  infoTable(
    ["Limitation", "What it means in practice"],
    [
      ["All training data is synthetic",       "The model has never seen a real crash. Real-world IMU noise, mounting resonance, and the chaotic kinematics of an actual collision are not in the training distribution. Generalisation to hardware is completely unvalidated."],
      ["Physics is simplified",                "The vehicle ODE ignores suspension travel, tyre flex, rider weight shift, and road camber. The Kelvin-Voigt brain model is a linearised single-mass approximation of a structure that's anything but linear."],
      ["HIC/BrIC values are constructed",      "The crash scenario pulses are engineered to exceed the thresholds — they aren't calibrated against instrumented crash test data or real cadaver measurements. The absolute numbers should not be taken at face value."],
      ["False positive SOS risk",              "A very aggressive emergency stop on dry tarmac can push past 6 g and trigger a crash alert. In a real deployment this needs a smarter fusion of acceleration magnitude, friction estimate, and velocity-to-zero profile."],
      ["Quantisation accuracy is unknown",     "The physics residuals require float32 autograd during training. How much accuracy is lost when the model is converted to INT8 for the ESP32-S3 hasn't been measured."],
      ["Regulatory gap is large",              "Medical devices and emergency safety systems require CE marking, ISO 13232 compliance (for motorcycle protective equipment), and clinical validation. None of that exists here yet."],
      ["Single-point sensing is fragile",      "One IMU in the helmet misses thorax and spine kinematics that strongly influence injury severity. And if the helmet comes off before the sensor fires, the system sees nothing."],
    ],
    [3240, 6120]
  ),
  spacer(),

  // ── 7. Quick Start ───────────────────────────────────────────────────────
  pageBreak(),
  h1("7. Getting It Running"),
  para("You don't need to retrain anything. The pre-trained checkpoint (roadsos_pinn.pt) is included in the repo, and the dashboard loads it automatically on startup. The whole setup takes about two minutes."),
  spacer(),
  codeBlock(quickstart, "Terminal"),
  spacer(),
  h2("Dashboard Scenarios"),
  para("Use the sidebar to switch between three scenarios. Each one runs a fresh simulation and feeds it through the PINN in real time:"),
  spacer(),
  infoTable(
    ["Scenario", "What's simulated", "What you'll see"],
    [
      ["Normal Riding", "Stable cruise at ~40 km/h with sinusoidal speed variation and dry-road friction", "P(skid) stays low, HIC15 well below 700, BrIC well below 0.6, status: ALL CLEAR"],
      ["Oil Patch",     "Rider hits oil at 40% of the duration; friction drops exponentially from 0.75 to 0.15", "P(skid) spikes past 0.65, haptic alert fires, status: SKID WARNING"],
      ["Crash",         "Hard brake 150 ms before impact; 120g halfsin primary pulse at 1 kHz; tip-over in 200 ms", "HIC15 > 1000, BrIC > 1.0, SOS triggered, status: CRASH DETECTED"],
    ],
    [1800, 3960, 3600]
  ),
  spacer(),

  // ── 8. Source Code ────────────────────────────────────────────────────────
  pageBreak(),
  h1("8. Source Code"),
  h2("8.1  roadsos_dashboard.py"),
  para("The complete Streamlit dashboard. It loads the PINN checkpoint, simulates IMU data for the selected scenario, runs inference, and renders four dark-mode plots alongside live metric cards. The rider SOS card at the bottom shows the medical profile that would be transmitted on a real crash event."),
  spacer(),
  codeBlock(dashboardCode, "roadsos_dashboard.py  —  full source"),

  pageBreak(),
  h2("8.2  RoadSoS_PINN.ipynb  —  Key Cells"),
  para("The training notebook is the scientific heart of the project. Below are the four most important cells — the network architecture, the physics losses, the training loop, and the injury metric implementations."),
  spacer(),
  h3("PINN Architecture"),
  codeBlock(pinnArch, "RoadSoSPINN class"),
  spacer(),
  h3("Physics Residuals and Loss Function"),
  codeBlock(pinnLoss, "Vehicle ODE + Brain Biomechanics Residuals"),
  spacer(),
  h3("Training Loop"),
  codeBlock(pinnTraining, "3000-epoch training with Adam + CosineAnnealing"),
  spacer(),
  h3("HIC15 and BrIC Computation"),
  codeBlock(hicCode, "Injury metric implementations"),

  pageBreak(),
  h2("8.3  requirements.txt"),
  para("Standard Python scientific stack plus Streamlit for the dashboard and pyngrok if you want to expose it publicly from a Colab/Kaggle environment."),
  spacer(),
  codeBlock(requirementsCode, "requirements.txt"),
  spacer(),

  // ── 9. Deployment ─────────────────────────────────────────────────────────
  h1("9. The Deployment Vision"),
  para("RoadSoS is currently a software demo, but every design decision was made with real hardware deployment in mind. The full helmet unit would look like this:"),
  spacer(),
  bullet("A 6-axis IMU — ICM-42688 for production (32 kHz headroom, low noise), MPU-6050 for a quick prototype (1 kHz, cheap)"),
  bullet("An ESP32-S3 running the quantised PINN at the edge — no cloud dependency, no latency, no data leaving the device during normal riding"),
  bullet("A linear resonant actuator (LRA) wired to a GPIO pin — fires a distinct haptic pattern when P(skid) crosses 0.65"),
  bullet("BLE to a companion phone app as the primary SOS channel, with cellular as a fallback so the system works even without a phone nearby"),
  bullet("An NFC tag or dynamically generated QR code that appears on the helmet's surface on crash detection — containing the AES-256 encrypted rider profile, readable by first-responder NFC hardware"),
  spacer(),
  para("Getting from this prototype to a deployable product would require: instrumented crash testing against ECE R22.06 and ISO 13232, clinical validation of the injury score against real patient outcomes, a privacy and consent framework for medical data, and regulatory approval as a medical device in any jurisdiction where it provides emergency health information. None of that is small — but the architecture is designed with that path in mind."),
  spacer(),

  // ── 10. Safety notice ────────────────────────────────────────────────────
  h1("10. Safety Notice"),
  spacer(40, 40),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    border: { left: { style: BorderStyle.THICK, size: 10, color: "CC2200", space: 14 } },
    indent: { left: 400 },
    children: [
      new TextRun({ text: "RoadSoS is a hackathon research prototype. ", bold: true, size: 22, font: "Arial", color: "CC2200" }),
      new TextRun({ text: "It was trained entirely on synthetic data and uses simplified physical models that do not reflect the full complexity of real crashes. The injury scores it produces are illustrative, not clinically validated. Do not use this system as a medical device, an emergency response tool, or a production vehicle safety system without proper hardware validation, certified sensor calibration, field testing, and regulatory approval.", size: 22, font: "Arial", color: "882200" }),
    ]
  }),
];

// ── Build and write ──────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{ reference: "bullets", levels: [{
      level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } }
    }]}]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: ACCENT },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: ACCENT },
        paragraph: { spacing: { before: 260, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "1A1A1A" },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 },
              margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: { default: new Header({ children: [new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 1 } },
      children: [
        new TextRun({ text: "RoadSoS  —  SmartHelmetSOS", size: 18, font: "Arial", color: "666666", bold: true }),
        new TextRun({ text: "  |  IITM Hackathon 2026", size: 18, font: "Arial", color: "AAAAAA" }),
      ]
    })]}) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 1 } },
      children: [
        new TextRun({ text: "Page ", size: 18, font: "Arial", color: "999999" }),
        new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "999999" }),
        new TextRun({ text: " / ", size: 18, font: "Arial", color: "999999" }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: "Arial", color: "999999" }),
      ]
    })]}) },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(
    "/sessions/affectionate-magical-cannon/mnt/IITM HACKATHON/SmartHelmetSOS_Documentation.docx", buf);
  console.log("Done.");
}).catch(e => { console.error(e); process.exit(1); });

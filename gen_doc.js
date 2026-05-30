const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat
} = require('/usr/local/lib/node_modules_global/lib/node_modules/docx');
const fs = require('fs');

const ACCENT = "005B96";
const CODEBG = "1E1E1E";
const THBG   = "003366";
const ROWALT = "EBF2FA";

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160 },
    children: [new TextRun({ text, bold: true, size: 36, color: ACCENT, font: "Arial" })]
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: ACCENT, font: "Arial" })]
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 180, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: "333333", font: "Arial" })]
  });
}
function para(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22, font: "Arial" })]
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, font: "Arial" })]
  });
}
function spacer() {
  return new Paragraph({ spacing: { before: 80, after: 80 }, children: [] });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function codeBlock(code, label) {
  const lines = code.split('\n');
  const border = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const rows = [];
  if (label) {
    rows.push(new TableRow({
      children: [new TableCell({
        borders,
        shading: { fill: "2D2D2D", type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 40, left: 160, right: 160 },
        width: { size: 9360, type: WidthType.DXA },
        children: [new Paragraph({
          children: [new TextRun({ text: label, bold: true, size: 18, color: "AAAAAA", font: "Courier New" })]
        })]
      })]
    }));
  }
  rows.push(new TableRow({
    children: [new TableCell({
      borders,
      shading: { fill: CODEBG, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 200, right: 160 },
      width: { size: 9360, type: WidthType.DXA },
      children: lines.map(line =>
        new Paragraph({
          spacing: { before: 0, after: 0, line: 240, lineRule: "auto" },
          children: [new TextRun({ text: line === '' ? ' ' : line, size: 18, color: "D4D4D4", font: "Courier New" })]
        })
      )
    })]
  }));
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], rows });
}

function infoTable(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => new TableCell({
          borders, width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: THBG, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: h, size: 20, font: "Arial", bold: true, color: "FFFFFF" })] })]
        }))
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((cell, ci) => new TableCell({
          borders, width: { size: colWidths[ci], type: WidthType.DXA },
          shading: { fill: ri % 2 === 1 ? ROWALT : "FFFFFF", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: cell, size: 20, font: "Arial" })] })]
        }))
      }))
    ]
  });
}

// ── Code strings ──────────────────────────────────────────────────────────────

const dashboardCode = `import os, streamlit as st, torch, torch.nn as nn, numpy as np, matplotlib.pyplot as plt

st.set_page_config(page_title="RoadSoS", page_icon="helmet", layout="wide")
plt.style.use("dark_background")

G=9.81; M_TOTAL=225; WHEELBASE=1.35; M_BRAIN=1.4; K_BRAIN=2.1e4; C_BRAIN=85
MU_DRY=0.75; MU_WET=0.45; MU_OIL=0.15
BRIC_X=66.3; BRIC_Y=56.5; BRIC_Z=42.2; HIC_LOW=700; HIC_HIGH=1000
FS_N=100; FS_C=1000
CA="#00E5FF"; CW="#FFD600"; CR="#FF1744"; CG="#00E676"; BG="#0d0d0d"

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
    ar = np.sqrt(ax**2+ay**2+az**2)/G
    dt = 1/fs; mw = max(2, int(wms*1e-3/dt)); h = 0
    cs = np.cumsum(ar)
    for w in range(2, mw+1):
        ms = (cs[w:]-cs[:-w])/w
        vals = w*dt*(np.maximum(ms,0)**2.5)
        h = max(h, vals.max())
    return h

def bric(gx, gy, gz):
    return np.sqrt((np.max(np.abs(gx))/BRIC_X)**2 +
                   (np.max(np.abs(gy))/BRIC_Y)**2 +
                   (np.max(np.abs(gz))/BRIC_Z)**2)

def sim(sc, dur, fs, seed=42):
    np.random.seed(seed)
    t = np.linspace(0, dur, int(dur*fs)); n = len(t)
    if sc == 0:  # Normal Riding
        v  = 11.1+0.5*np.sin(0.3*t)+0.1*np.random.randn(n)
        th = 0.05*np.sin(0.2*t)+0.01*np.random.randn(n)
        mu = np.clip(MU_DRY+0.02*np.random.randn(n), 0.6, 0.9)
    elif sc == 1:  # Oil Patch
        pivot = int(0.4*n); v = 13.9+0.8*np.sin(0.3*t)
        mu = np.ones(n)*MU_DRY
        dec = np.exp(-np.arange(n-pivot)/(0.2*fs))
        mu[pivot:] = MU_OIL+(MU_DRY-MU_OIL)*dec[:n-pivot]
        mu = np.clip(mu, 0.05, 0.9)
        th = 0.05*np.sin(0.2*t); th[pivot:] += 0.3*(1-dec[:n-pivot])
    else:  # Crash
        impact_t = 0.25*dur; ii = int(impact_t*fs)
        pre = max(0, ii-int(0.15*fs)); ii2 = ii+int(0.35*fs)
        v = np.ones(n)*16.7
        v[pre:ii] = np.linspace(16.7, 16.7*0.65, ii-pre)
        stop_w = int(0.05*fs)
        v[ii:ii+stop_w] = np.linspace(16.7*0.65, 0.0, stop_w)
        v[ii+stop_w:] = 0.0
        mu = np.ones(n)*MU_DRY
        mu[pre:ii] = np.linspace(MU_DRY, MU_OIL+0.05, ii-pre)
        mu[ii:] = MU_OIL
        mu = np.clip(mu+0.01*np.random.randn(n), 0.01, 0.9)
        th = np.zeros(n); th[pre:ii] = 0.05*np.linspace(0,1,ii-pre)
        tip_w = int(0.20*fs)
        th[ii:ii+tip_w] = np.clip(np.linspace(0,np.pi/2,tip_w),0,np.pi/2)
        th[ii+tip_w:] = np.pi/2
        th = np.clip(th+0.008*np.random.randn(n),0,np.pi/2)
    ax = np.diff(v,prepend=v[0])*fs+0.1*np.random.randn(n)
    ay = v*np.gradient(th,1/fs)+0.1*np.random.randn(n)
    az = G*np.cos(th)+0.05*np.random.randn(n)
    gx = np.gradient(th,1/fs)+0.02*np.random.randn(n)
    gy = 0.05*np.sin(0.1*t)+0.01*np.random.randn(n)
    gz = 0.03*np.cos(0.15*t)+0.01*np.random.randn(n)
    if sc == 2:
        ipw=int(0.025*fs); spw=int(0.015*fs)
        pulse1=np.zeros(n); pulse2=np.zeros(n)
        if ii+ipw<n: pulse1[ii:ii+ipw]=120*G*np.sin(np.linspace(0,np.pi,ipw))
        if ii2+spw<n: pulse2[ii2:ii2+spw]=30*G*np.sin(np.linspace(0,np.pi,spw))
        ax+=pulse1+pulse2; az-=0.25*pulse1
        ff_s=ii+ipw; ff_e=ff_s+int(0.03*fs)
        if ff_e<n: az[ff_s:ff_e]*=0.1
        apw=int(0.030*fs)
        if ii+apw<n:
            gx[ii:ii+apw]+=78*np.sin(np.linspace(0,np.pi,apw))
            gy[ii:ii+apw]+=62*np.sin(np.linspace(0,np.pi,apw))
            gz[ii:ii+apw]+=48*np.sin(np.linspace(0,np.pi,apw))
    return t, ax, ay, az, gx, gy, gz, v, th, mu

# Sidebar controls
st.sidebar.title("RoadSoS Controls")
sc_name = st.sidebar.selectbox("Scenario",["Normal Riding","Oil Patch","Crash"])
sc  = {"Normal Riding":0,"Oil Patch":1,"Crash":2}[sc_name]
fs  = FS_C if sc==2 else FS_N
dur = st.sidebar.slider("Duration (s)",1.0,15.0,8.0 if sc<2 else 2.0,0.5)
st.sidebar.markdown("---"); st.sidebar.markdown("**Rider Profile**")
bg  = st.sidebar.selectbox("Blood Group",["O+","O-","A+","A-","B+","B-","AB+","AB-"])
alg = st.sidebar.text_input("Allergies","None")
ec  = st.sidebar.text_input("Emergency Contact","+91-XXXXXXXXXX")

# Inference
model,nm,ns = load_model()
t,ax,ay,az,gx,gy,gz,v,th,mu = sim(sc,dur,fs)
X = np.c_[t,ax,ay,az,gx,gy,gz]
Xn = (X-nm)/(ns+1e-8)
Xt = torch.tensor(Xn,dtype=torch.float32)
with torch.no_grad(): o = model.out(Xt)
mu_p = o["mu_eff"].numpy().flatten()
Psk  = np.clip((MU_WET-mu_p)/MU_WET,0,1)
ares = np.sqrt(ax**2+ay**2+az**2)/G
hv   = hic15(ax,ay,az,fs); bv = bric(gx,gy,gz)
inj  = min(0.6*hv/HIC_HIGH+0.4*bv,1.0)

# Alert banner
crash_det=(sc==2 or ares.max()>6); skid_det=(Psk.max()>0.65 and not crash_det)
ac=CR if crash_det else(CW if skid_det else CG)
at="CRASH DETECTED - SOS FIRED" if crash_det else("SKID WARNING" if skid_det else "SAFE")
st.markdown(f"<h2 style='color:{ac};'>{at}</h2>",unsafe_allow_html=True)

# Metrics
c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Peak Accel",f"{ares.max():.1f} g",">6g" if ares.max()>6 else "OK")
c2.metric("P(skid) max",f"{Psk.max():.2f}","HIGH" if Psk.max()>0.65 else "LOW")
c3.metric("HIC15",f"{hv:.0f}","DANGER" if hv>700 else "OK")
c4.metric("BrIC",f"{bv:.3f}","CRITICAL" if bv>1 else "OK")
c5.metric("Injury Score",f"{inj:.2f}","SEVERE" if inj>0.7 else("MOD" if inj>0.3 else "LOW"))

# Rider card (SOS medical release)
st.markdown("---")
st.markdown(
    f"<div style='background:#111;padding:16px;border-radius:10px;border:1px solid {CA};'>"
    f"<h4 style='color:{CA};'>Rider Medical Profile - Transmitted on SOS</h4>"
    f"<p>Blood: <b>{bg}</b> | Allergies: <b>{alg}</b> | Emergency: <b>{ec}</b></p>"
    f"<p style='color:gray;font-size:12px;'>Encrypted on ESP32-S3. Released via NFC/QR on crash detection.</p>"
    f"</div>",unsafe_allow_html=True)`;

const pinnArch = `class RoadSoSPINN(nn.Module):
    """
    Input  (7): [t, ax, ay, az, gx, gy, gz]
    Output (6): [v, theta, mu_eff, x_brain, y_brain, z_brain]

    tanh    : smooth higher-order derivatives for physics residuals
    Xavier  : stable variance through 6-layer tanh stack
    sigmoid : enforces mu_eff in (0, 1) — physical range
    """
    def __init__(self, hidden_layers=6, hidden_width=128):
        super().__init__()
        dims = [7] + [hidden_width]*hidden_layers + [6]
        layers = []
        for i in range(len(dims)-1):
            layers.append(nn.Linear(dims[i], dims[i+1]))
            if i < len(dims)-2: layers.append(nn.Tanh())
        self.net = nn.Sequential(*layers)
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def get_outputs(self, x):
        o = self.net(x)
        return {"v": o[:,0:1], "theta": o[:,1:2],
                "mu_eff": torch.sigmoid(o[:,2:3]),
                "x_brain": o[:,3:4], "y_brain": o[:,4:5], "z_brain": o[:,5:6]}`;

const pinnLoss = `def residual_vehicle(outs, x):
    # Two-wheeler ODEs via autograd
    # (1)  M * dv/dt + mu_eff * M * G = 0
    # (2)  dtheta/dt - v * sin(theta) / L = 0
    dv_dt     = grad(outs["v"].sum(),     x, create_graph=True)[0][:, 0:1]
    dtheta_dt = grad(outs["theta"].sum(), x, create_graph=True)[0][:, 0:1]
    R_v     = (M_TOTAL*dv_dt + outs["mu_eff"]*M_TOTAL*G) / (M_TOTAL*G)
    R_theta = dtheta_dt - outs["v"]*torch.sin(outs["theta"])/WHEELBASE
    return R_v, R_theta

def residual_biomechanics(outs, x):
    # Kelvin-Voigt brain ODE per axis:
    #   M_b * x_b'' + C * x_b' + K * x_b = M_b * a_helmet
    Rs = []
    for x_b, a_h in zip(
        [outs["x_brain"], outs["y_brain"], outs["z_brain"]],
        [x[:,1:2], x[:,2:3], x[:,3:4]]
    ):
        x_b_t  = grad(x_b.sum(),   x, create_graph=True)[0][:, 0:1]
        x_b_tt = grad(x_b_t.sum(), x, create_graph=True)[0][:, 0:1]
        Rs.append((M_BRAIN*x_b_tt + C_BRAIN*x_b_t
                   + K_BRAIN*x_b - M_BRAIN*a_h) / K_BRAIN)
    return Rs

def pinn_loss(model, x_batch, y_batch, lam):
    x_batch = x_batch.clone().requires_grad_(True)
    outs    = model.get_outputs(x_batch)
    pred    = torch.cat([outs["v"], outs["theta"], outs["mu_eff"]], dim=1)
    L_d     = nn.functional.mse_loss(pred, y_batch)
    R_v, R_th = residual_vehicle(outs, x_batch)
    L_veh   = (R_v**2).mean() + (R_th**2).mean()
    L_bio   = sum((R**2).mean() for R in residual_biomechanics(outs, x_batch))
    return lam["data"]*L_d + lam["vehicle"]*L_veh + lam["bio"]*L_bio`;

const pinnTraining = `model = RoadSoSPINN().to(DEVICE)
opt   = optim.Adam(model.parameters(), lr=1e-3)
sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=3000, eta_min=1e-5)
lam   = {"data": 1.0, "vehicle": 0.1, "bio": 0.05}

for ep in range(1, 3001):
    model.train()
    for xb, yb in loader:
        opt.zero_grad()
        loss = pinn_loss(model, xb, yb, lam)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    sched.step()

torch.save({"model_state": model.state_dict(),
            "norm_mean":   norm.mean,
            "norm_std":    norm.std}, "roadsos_pinn.pt")`;

const hicCode = `def compute_hic15(ax, ay, az, fs, window_ms=15):
    # Head Injury Criterion over 15ms window (ECE 22.06)
    a_res = np.sqrt(ax**2 + ay**2 + az**2) / G
    dt    = 1.0 / fs
    max_w = max(2, int(window_ms * 1e-3 / dt))
    hic   = 0.0; cs = np.cumsum(a_res)
    for w in range(2, max_w+1):
        means = (cs[w:] - cs[:-w]) / w
        vals  = w * dt * (np.maximum(means, 0) ** 2.5)
        hic   = max(hic, vals.max())
    return hic

def compute_bric(gx, gy, gz):
    # Brain Rotational Injury Criterion (NHTSA cadaver study)
    return np.sqrt(
        (np.max(np.abs(gx))/BRIC_X)**2 +
        (np.max(np.abs(gy))/BRIC_Y)**2 +
        (np.max(np.abs(gz))/BRIC_Z)**2)

def injury_label(hic, bric):
    score = min(0.6*hic/HIC_HIGH + 0.4*bric, 1.0)
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

const quickstart = `# 1. Create and activate virtual environment
python -m venv .venv
.venv\\Scripts\\Activate.ps1      # Windows PowerShell
source .venv/bin/activate         # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run dashboard (loads pre-trained roadsos_pinn.pt automatically)
streamlit run roadsos_dashboard.py
# -> http://localhost:8501

# 4. Retrain model (optional, requires GPU recommended)
jupyter notebook RoadSoS_PINN.ipynb`;

// ── Document children ─────────────────────────────────────────────────────────
const children = [
  // Title page
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 160 },
    children: [new TextRun({ text: "RoadSoS  /  SmartHelmetSOS", bold: true, size: 56, font: "Arial", color: ACCENT })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 },
    children: [new TextRun({ text: "Physics-Informed Neural Network for Two-Wheeler Crash Detection & Head-Injury Risk Estimation", size: 26, font: "Arial", color: "444444", italics: true })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 },
    children: [new TextRun({ text: "IITM Hackathon 2026  |  github.com/ShauryaAttreya37/SmartHelmetSOS", size: 20, font: "Arial", color: "888888" })]
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 40, after: 60 },
    children: [new TextRun({ text: "Python 82.4%  |  Jupyter Notebook 17.6%  |  PyTorch  |  Streamlit", size: 20, font: "Arial", color: "AAAAAA" })]
  }),

  pageBreak(),

  // 1. Overview
  h1("1. Project Overview"),
  para("RoadSoS is a two-wheeler crash detection and head-injury risk demonstration built around a Physics-Informed Neural Network (PINN). It uses simulated helmet IMU data to estimate skid probability, effective friction loss, and two internationally recognised injury signals — HIC15 and BrIC — in real time via a Streamlit dashboard."),
  spacer(),
  para("The model is physics-informed because training combines ordinary data loss with residual losses based on two simplified physical systems: tire-road friction and lean dynamics for a two-wheeler, and Kelvin-Voigt spring-mass-damper dynamics for helmet-to-brain motion. This makes the system more than a plain sensor classifier — outputs remain physically consistent with the governing ODEs used during training."),
  spacer(),
  h2("Repository Files"),
  infoTable(
    ["File", "Description"],
    [
      ["roadsos_dashboard.py", "Streamlit dashboard — interactive inference and dark-mode visualisation"],
      ["RoadSoS_PINN.ipynb",   "Training notebook — data generation, physics losses, and evaluation"],
      ["roadsos_pinn.pt",      "Trained model checkpoint (loaded by dashboard at startup)"],
      ["requirements.txt",     "Python package dependencies"],
      [".gitignore",           "Ignore rules for venvs, generated files, and future checkpoints"],
    ],
    [3240, 6120]
  ),
  spacer(),

  // 2. Sensors
  pageBreak(),
  h1("2. Sensor Specifics"),
  h2("2.1  IMU — Inertial Measurement Unit"),
  para("The system is designed around a 6-axis IMU (3-axis accelerometer + 3-axis gyroscope). Two hardware options are named in the deployment vision:"),
  spacer(),
  infoTable(
    ["Sensor", "DOF", "Max ODR", "Interface", "Notes"],
    [
      ["MPU-6050",  "6-axis", "1 kHz",   "I2C / SPI", "Low-cost; suitable for prototype; meets 1 kHz HIC requirement at limit"],
      ["ICM-42688", "6-axis", "32 kHz",  "SPI",       "High-precision; lower noise floor; preferred for production deployment"],
    ],
    [1800, 900, 1260, 1440, 3960]
  ),
  spacer(),
  h3("IMU Input Vector (7 features per timestep)"),
  codeBlock("t     — time (s)\nax    — linear acceleration X  (m/s2)   forward / braking axis\nay    — linear acceleration Y  (m/s2)   lateral lean axis\naz    — linear acceleration Z  (m/s2)   vertical / gravity axis\ngx    — angular velocity X     (rad/s)  roll rate\ngy    — angular velocity Y     (rad/s)  pitch rate\ngz    — angular velocity Z     (rad/s)  yaw rate", "PINN Input: shape [N, 7]"),
  spacer(),
  h2("2.2  Sampling Rates"),
  infoTable(
    ["Scenario", "Sample Rate", "Why"],
    [
      ["Normal Riding", "100 Hz (FS_NORMAL)", "Friction and lean dynamics evolve over 100+ ms — 100 Hz is sufficient"],
      ["Oil Patch",     "100 Hz (FS_NORMAL)", "Slip build-up is gradual (~200 ms) — 100 Hz captures it well"],
      ["Crash",         "1000 Hz (FS_CRASH)", "HIC15 computation requires >= 1 kHz per ECE 22.06 standard"],
    ],
    [2880, 2520, 4680]
  ),
  spacer(),
  h2("2.3  Edge Compute — ESP32-S3"),
  para("The ESP32-S3 is the on-helmet microcontroller of choice. Relevant capabilities:"),
  bullet("Dual-core Xtensa LX7 at 240 MHz — sufficient for quantised PINN inference at < 10 ms latency"),
  bullet("Wi-Fi 802.11 b/g/n + Bluetooth 5 BLE — wireless SOS trigger and data offload to paired phone"),
  bullet("Vector extension (AIE) — accelerates INT8 matrix ops in the quantised model"),
  bullet("On-chip AES-128/256 — encrypts rider medical profile before NFC / QR release"),
  bullet("GPIO for haptic LRA driver (skid warning) and LED status indicators"),
  spacer(),
  h2("2.4  Other Hardware Components"),
  infoTable(
    ["Component", "Role in System"],
    [
      ["Haptic actuator (LRA / ERM)", "Vibrates helmet shell when P(skid) > 0.65 to warn rider of low-friction surface"],
      ["BLE to paired phone",         "Primary SOS channel — forwards crash event + GPS co-ordinates to emergency contact"],
      ["Cellular fallback",           "Backup SOS path when phone is out of BLE range"],
      ["NFC / QR tag",               "Releases encrypted rider profile (blood group, allergies, emergency contact) to first responders on crash detection"],
    ],
    [3240, 6120]
  ),
  spacer(),

  // 3. Architecture
  pageBreak(),
  h1("3. Model Architecture"),
  h2("3.1  Network Summary"),
  infoTable(
    ["Property", "Value"],
    [
      ["Input features",    "[t, ax, ay, az, gx, gy, gz] — 7 scalars"],
      ["Output values",     "[v, theta, mu_eff, x_brain, y_brain, z_brain] — 6 scalars"],
      ["Architecture",      "Fully connected neural network"],
      ["Hidden layers",     "6"],
      ["Hidden width",      "128 neurons per layer"],
      ["Activation",        "tanh (smooth — required for autograd second derivatives in physics loss)"],
      ["Weight init",       "Xavier uniform; biases initialised to zero"],
      ["mu_eff constraint", "sigmoid applied to raw output — enforces physical range (0, 1)"],
      ["Framework",         "PyTorch"],
      ["Dashboard",         "Streamlit"],
      ["Trainable params",  "~131,000"],
    ],
    [3600, 5760]
  ),
  spacer(),
  h2("3.2  Physics Constraints"),
  para("Vehicle ODE (two-wheeler friction deceleration and lean kinematics):"),
  spacer(),
  codeBlock("M * dv/dt  +  mu_eff * M * G  =  0\n\ndtheta/dt  -  v * sin(theta) / L  =  0\n\nWhere:\n  M        = 225 kg  (rider 75 kg + bike 150 kg)\n  G        = 9.81 m/s2\n  L        = 1.35 m  (wheelbase)\n  mu_eff   = PINN-predicted effective friction coefficient\n  theta    = lean angle (rad)", "Vehicle ODE Residual"),
  spacer(),
  para("Kelvin-Voigt brain spring-mass-damper (applied independently per axis):"),
  spacer(),
  codeBlock("M_b * x_b''  +  C * x_b'  +  K * x_b  =  M_b * a_helmet\n\nWhere:\n  M_b  = 1.4 kg       (brain mass)\n  K    = 21000 N/m    (stiffness)\n  C    = 85 N.s/m     (damping -> natural freq ~19.5 Hz, concussion-risk band)\n  a_helmet = IMU linear acceleration on that axis", "Brain Biomechanical ODE"),
  spacer(),
  para("Total training loss:"),
  spacer(),
  codeBlock("L_total = 1.0  * L_data\n        + 0.1  * L_vehicle\n        + 0.05 * L_bio\n\nL_data    = MSE(predicted [v, theta, mu_eff], ground truth)\nL_vehicle = mean(R_v^2) + mean(R_theta^2)\nL_bio     = sum over 3 axes of mean(R_brain^2)", "Combined Loss Function"),
  spacer(),

  // 4. Injury metrics
  h1("4. Injury and Alert Thresholds"),
  infoTable(
    ["Signal", "Warning", "Critical", "Standard"],
    [
      ["HIC15 — Head Injury Criterion (15 ms window)", "700",  "1000", "ECE 22.06 motorcycle helmet standard"],
      ["BrIC — Brain Rotational Injury Criterion",     "0.6",  "1.0",  "NHTSA cadaver study, Takhounts 2013"],
      ["Skid probability P(skid)",                     "0.65", "—",    "PINN output via sigmoid mu_eff"],
      ["Peak resultant acceleration",                  "6 g",  "—",    "Empirical crash threshold"],
    ],
    [3600, 1260, 1260, 3240]
  ),
  spacer(),
  para("BrIC axis thresholds: gx = 66.3 rad/s (sagittal/pitch), gy = 56.5 rad/s (coronal/roll), gz = 42.2 rad/s (transverse/yaw)."),
  para("Composite injury score = min(0.6 x HIC15/1000 + 0.4 x BrIC, 1.0).  < 0.3: LOW;  0.3-0.7: MODERATE;  > 0.7: SEVERE."),
  spacer(),

  // 5. Use cases
  pageBreak(),
  h1("5. Use Cases"),
  h2("5.1  Primary Use Cases"),
  bullet("Real-time skid detection: PINN predicts mu_eff from IMU data each timestep; when P(skid) > 0.65, the haptic actuator vibrates the helmet shell, warning the rider of a low-friction surface such as wet asphalt or an oil patch."),
  bullet("Crash detection and automated SOS: When peak resultant acceleration exceeds 6 g (or the crash scenario flag is raised), the system fires an SOS signal over BLE/cellular, transmits GPS co-ordinates to the emergency contact, and releases the rider's encrypted medical profile via NFC/QR."),
  bullet("Head injury risk quantification: HIC15 and BrIC computed from the raw IMU stream give paramedics an immediate, standardised head-injury risk score — before hospital imaging is available."),
  bullet("Continuous friction surface monitoring: The dashboard displays PINN-predicted mu_eff overlaid against dry (0.75), wet (0.45), and oil (0.15) thresholds, providing real-time road-surface quality information useful for fleet telematics."),
  spacer(),
  h2("5.2  Secondary / Future Use Cases"),
  bullet("Crash reconstruction and insurance: Timestamped IMU logs, physics-consistent velocity profiles, and friction estimates support post-crash forensics for insurance claims and legal proceedings."),
  bullet("Rider coaching: Accumulated skid events, harsh-braking episodes, and injury-risk scores aggregated per rider over time produce a behaviour score for training feedback."),
  bullet("Urban road-surface mapping: Aggregate anonymised friction data from a fleet of helmet sensors could map road quality in real time, informing municipal maintenance schedules."),
  bullet("Pre-hospital triage optimisation: Severity scores transmitted with GPS allow emergency dispatch to pre-alert trauma units and prepare resources before the ambulance arrives."),
  spacer(),

  // 6. Pros and Cons
  h1("6. Pros and Cons"),
  h2("6.1  Advantages"),
  infoTable(
    ["Category", "Advantage"],
    [
      ["Physics grounding",   "Physics residuals constrain outputs to be consistent with known dynamics, reducing overfitting and improving robustness beyond training distribution."],
      ["Multi-output single pass", "One forward pass yields velocity, lean angle, friction, and 3-axis brain displacement simultaneously — no stacked model latency."],
      ["Edge-deployable",     "131k parameters; quantises to < 1 MB; runs < 10 ms on ESP32-S3 — no cloud round-trip required for real-time alerts."],
      ["Standards-aligned",   "HIC15 follows ECE 22.06; BrIC thresholds from NHTSA cadaver study — outputs are directly interpretable by safety engineers and clinicians."],
      ["GPS-independent",     "Crash and skid detection relies solely on the helmet IMU, so it operates in GPS-denied environments (tunnels, urban canyons)."],
      ["Privacy-preserving",  "Medical profile is stored encrypted on-device and transmitted only on crash detection, minimising data exposure during normal riding."],
    ],
    [2520, 6840]
  ),
  spacer(),
  h2("6.2  Limitations and Risks"),
  infoTable(
    ["Category", "Limitation / Risk"],
    [
      ["Synthetic data only",         "All training data is simulated. Real-world sensor noise, drift, mounting vibration, and non-idealised crash kinematics are not captured — hardware generalisation is unvalidated."],
      ["Simplified physics",          "The vehicle ODE neglects suspension, tyre flex, rider weight shift, and road camber. The Kelvin-Voigt model is a linearised single-mass approximation of a complex viscoelastic structure."],
      ["No real crash corpus",        "HIC and BrIC pulse magnitudes are calibrated to exceed thresholds by construction, not validated against instrumented crash tests or cadaver data."],
      ["Quantisation accuracy loss",  "PINN physics residuals require float32 for accurate autograd during training; INT8 post-training quantisation may degrade friction and brain-displacement accuracy."],
      ["False positive SOS",          "Aggressive braking on dry road can exceed 6 g and trigger an erroneous crash alert and SOS signal."],
      ["Regulatory gap",              "CE and FDA medical device regulations require clinical validation and certified sensor calibration before deployment as an emergency safety system."],
      ["Single-point sensing",        "A single helmet IMU misses thorax and spine kinematics that influence injury severity, and is rendered useless if the helmet is ejected before the sensor fires."],
    ],
    [2700, 6660]
  ),
  spacer(),

  // 7. Quick start
  pageBreak(),
  h1("7. Quick Start"),
  codeBlock(quickstart, "Terminal"),
  spacer(),
  h2("Dashboard Scenarios"),
  infoTable(
    ["Scenario", "Description", "Key Signals"],
    [
      ["Normal Riding", "Stable cruise ~40 km/h with sinusoidal speed variation and dry-road friction", "P(skid) < 0.65, HIC15 < 700, BrIC < 0.6, Status: SAFE"],
      ["Oil Patch",     "Rider hits oil patch at 40% of duration; friction drops from 0.75 to 0.15 exponentially", "P(skid) > 0.65, haptic alert fires, Status: SKID WARNING"],
      ["Crash",         "Hard brake 150 ms before impact; 120g halfsin primary pulse at 1 kHz; tip-over in 200 ms", "HIC15 > 1000, BrIC > 1.0, SOS fired, Status: CRASH DETECTED"],
    ],
    [2160, 4320, 2880]
  ),
  spacer(),

  // 8. Source code
  pageBreak(),
  h1("8. Source Code"),
  h2("8.1  roadsos_dashboard.py"),
  para("Full Streamlit dashboard. Loads the saved PINN checkpoint, runs inference against a selected scenario, and renders live metrics and four dark-mode matplotlib plots."),
  spacer(),
  codeBlock(dashboardCode, "roadsos_dashboard.py"),

  pageBreak(),
  h2("8.2  RoadSoS_PINN.ipynb  (Key Cells)"),
  spacer(),
  h3("PINN Architecture"),
  codeBlock(pinnArch, "Cell: RoadSoSPINN class"),
  spacer(),
  h3("Physics Loss Functions"),
  codeBlock(pinnLoss, "Cell: Vehicle ODE + Brain Biomechanics Residuals"),
  spacer(),
  h3("Training Loop"),
  codeBlock(pinnTraining, "Cell: Training (3000 epochs, Adam + CosineAnnealing)"),
  spacer(),
  h3("Injury Metric Computation"),
  codeBlock(hicCode, "Cell: HIC15 and BrIC"),

  pageBreak(),
  h2("8.3  requirements.txt"),
  codeBlock(requirementsCode, "requirements.txt"),
  spacer(),

  // 9. Deployment vision
  h1("9. Deployment Vision"),
  para("The software demo is designed around a possible helmet-mounted safety system. The full hardware stack would consist of:"),
  bullet("6-axis IMU: ICM-42688 at 1–32 kHz for production; MPU-6050 at 1 kHz for prototyping"),
  bullet("Edge compute: ESP32-S3 with on-chip AES encryption co-processor"),
  bullet("Haptic feedback: LRA driven by GPIO PWM when P(skid) > 0.65"),
  bullet("Connectivity: BLE primary channel to paired phone; cellular fallback for SOS without phone proximity"),
  bullet("Emergency data release: AES-encrypted NFC tag or dynamic QR code generated on crash detection, readable by authorised first-responder hardware"),
  spacer(),
  para("Real deployment requirements: hardware validation with calibrated sensors, field testing across terrain types and realistic crash speeds, privacy and consent framework for medical data storage, and regulatory review under ECE R22.06, ISO 13232, and applicable CE / FDA Medical Devices Regulation."),
  spacer(),

  // 10. Safety notice
  h1("10. Safety Notice"),
  new Paragraph({
    spacing: { before: 80, after: 80 },
    border: { left: { style: BorderStyle.THICK, size: 8, color: "FF1744", space: 12 } },
    indent: { left: 360 },
    children: [new TextRun({
      text: "RoadSoS is a research and hackathon prototype. It uses entirely synthetic data and simplified physics models. Do not use it as a medical device, emergency response system, or production vehicle safety system without proper validation, certification, and real-world testing.",
      size: 22, font: "Arial", color: "CC0000", bold: true
    })]
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
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: ACCENT },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "333333" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 },
              margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: { default: new Header({ children: [new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 1 } },
      children: [new TextRun({ text: "RoadSoS — SmartHelmetSOS  |  IITM Hackathon 2026", size: 18, font: "Arial", color: "888888" })]
    })]}) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 1 } },
      children: [
        new TextRun({ text: "Page ", size: 18, font: "Arial", color: "888888" }),
        new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "888888" }),
        new TextRun({ text: " of ", size: 18, font: "Arial", color: "888888" }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: "Arial", color: "888888" }),
      ]
    })]}) },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/sessions/affectionate-magical-cannon/mnt/IITM HACKATHON/SmartHelmetSOS_Documentation.docx", buf);
  console.log("Done.");
}).catch(e => { console.error(e); process.exit(1); });

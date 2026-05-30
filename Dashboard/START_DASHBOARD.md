# Start the RoadSoS Streamlit Dashboard

Use these steps from the project folder:

```powershell
cd "C:\Users\shaur\OneDrive\Documents\IITM HACKATHON"
```

## 1. Create a Python environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation, run this command in the same folder instead:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

## 2. Install dependencies

```powershell
python -m pip install streamlit torch numpy matplotlib pandas scipy pyngrok
```

For local dashboard-only use, the key packages are `streamlit`, `torch`, `numpy`, and `matplotlib`.

## 3. Generate the dashboard file if needed

The Streamlit app is written from `RoadSoS_PINN.ipynb` using the cell titled:

```text
StreamLit Dashboard Code
```

Run the notebook from top to bottom at least once if either of these files is missing:

```text
roadsos_dashboard.py
roadsos_pinn.pt
```

`roadsos_pinn.pt` is the trained PINN model checkpoint that the dashboard loads at startup.

## 4. Start the dashboard locally

```powershell
streamlit run roadsos_dashboard.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## 5. Start from Google Colab

In Colab, run the notebook cells through the final launch cell:

```python
proc = subprocess.Popen([
    "streamlit", "run", "roadsos_dashboard.py",
    "--server.port", "8501",
    "--server.headless", "true",
])
url = ngrok.connect(8501)
print("Dashboard URL:", url)
```

Open the printed ngrok URL to view the live dashboard.

## Quick Troubleshooting

- `FileNotFoundError: roadsos_pinn.pt`: run the training/save cells in `RoadSoS_PINN.ipynb`.
- `streamlit is not recognized`: activate `.venv`, then reinstall dependencies.
- Dashboard opens but model fails to load: keep `roadsos_dashboard.py` and `roadsos_pinn.pt` in the same folder.

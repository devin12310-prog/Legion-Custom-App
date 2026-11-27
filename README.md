# Legion Custom App

Personal custom launcher + quick settings overlay for the **first-gen Lenovo Legion Go (Z1 Extreme)**.

## Features

### Home Page
- Scans Steam library for installed games
- Simple game cards with Launch button

### Right Quick Menu (clear sections)
1. **Performance** – Quiet / Balanced / Performance / Custom
2. **TDP Limit** – Slider + Apply via RyzenAdj
3. **Display** – Legion Go resolutions (1600x1000 native + others), refresh, brightness
4. **Scalers & Frame Gen** – FSR / XeSS / OptiScaler / DLSS + Lossless Scaling / AFMF / OptiFG / XeFG
5. **Legion Go Mapper** – Y1/Y2/Y3 + rear button profiles
6. **Drivers & Updates** – Lenovo + AMD + this repo
7. **System** – Live stats

### Buttons
- **Top-right Quick Menu button** opens the right panel
- Legion button → map with PowerToys / AutoHotkey (see below)
- Hotkeys: `Ctrl+Shift+L` or `F1`

---

## Download & Run

1. Download ZIP from this repo
2. Extract
3. Install Python 3.11+
4. In the folder:

```powershell
pip install -r requirements.txt
python main.py
```

---

## Official OptiScaler & Frame Gen Links

- **OptiScaler** (main tool): https://github.com/optiscaler/OptiScaler
- **OptiScaler Releases**: https://github.com/optiscaler/OptiScaler/releases
- **OptiScaler Wiki** (install guide): https://github.com/optiscaler/OptiScaler/wiki

Lossless Scaling is a paid Steam app (AppID 993090). The menu has a one-click launch button for it.

---

## Mapping the Legion Button

Use **Microsoft PowerToys** → Keyboard Manager to remap the Legion button to launch:

```
python "C:\path\to\LegionCustomApp\main.py"
```

Or create a shortcut and map to that.

---

## Optional Tools

- Place `ryzenadj.exe` next to `main.py` for real TDP control
- Drop OptiScaler files into the `OptiScaler` folder the app creates

Repo: https://github.com/devin12310-prog/Legion-Custom-App

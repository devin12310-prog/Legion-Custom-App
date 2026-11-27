# Legion Custom App

Personal custom launcher + quick settings overlay for the **first-gen Lenovo Legion Go (Z1 Extreme)**.

Inspired by Legion Space / GoTweaks style UX, but 100% original code made for you.

## Features

### Home Page
- Scans Steam library for installed games
- Simple game cards with Launch button
- Refresh button

### Right Quick Menu (clear sections)
1. **Performance** – Quiet / Balanced / Performance / Custom presets
2. **TDP Limit** – Slider + Apply via RyzenAdj
3. **Display** – Legion Go resolutions (1600x1000 native + others), refresh rate, brightness
4. **Scalers & Frame Gen** – FSR / XeSS / OptiScaler / DLSS spoof + Lossless Scaling / AFMF / OptiFG
5. **Legion Go Mapper** – Profile selector for Y1/Y2/Y3 + rear buttons
6. **Drivers & Updates** – Quick links to Lenovo support + AMD + this GitHub repo
7. **System** – Live CPU/RAM + current settings

### Buttons
- **Top-right "Quick Menu" button** → opens/closes the right panel
- **Legion button** → see setup instructions below
- Hotkeys: `Ctrl+Shift+L` or `F1` to toggle menu, `Esc` to close

---

## How to Install (one download)

1. Go to the Releases page (or download the ZIP of the main branch)
2. Extract the folder anywhere (example: `C:\LegionCustomApp`)
3. Install **Python 3.11+** from python.org (check "Add python.exe to PATH")
4. Open PowerShell **inside the extracted folder** and run:

```powershell
pip install -r requirements.txt
python main.py
```

---

## Mapping the Legion Button (recommended)

The physical Legion button is best mapped with a free tool:

### Option A – PowerToys (easy)
1. Install Microsoft PowerToys
2. Go to Keyboard Manager → Remap a key
3. Map the Legion button (it usually shows up as a special key) to launch:
   ```
   python "C:\path\to\LegionCustomApp\main.py"
   ```
   Or create a shortcut to `main.py` and map to that.

### Option B – AutoHotkey (more control)
Create a small `.ahk` script that launches the app (or launches it with `--menu` to open the right panel immediately).

You can also create a desktop shortcut and pin it, then map the Legion button to that shortcut.

---

## Optional: RyzenAdj for real TDP control

1. Download a recent RyzenAdj build
2. Place `ryzenadj.exe` next to `main.py`
3. The "Apply TDP" button will then work

---

## Optional: OptiScaler

Create an `OptiScaler` folder next to `main.py` and drop the OptiScaler files there. The menu has a quick button to open that folder.

---

## Repository

https://github.com/devin12310-prog/Legion-Custom-App

This is your personal project. Feel free to edit anything.

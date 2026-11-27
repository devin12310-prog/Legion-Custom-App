# Legion Custom App  v1.1.0

Custom Decky-style quick settings + game launcher for the **first-gen Lenovo Legion Go (Z1 Extreme)**.

---

## One-time setup

1. Make sure **Python 3.10+** is installed (Microsoft Store or python.org — check "Add to PATH")
2. Download the ZIP from GitHub → extract it anywhere
3. Double-click **`install.bat`**
   - Creates a Start Menu entry called **Legion Custom**
   - Installs required packages
4. Launch from Start Menu or double-click **`run.bat`**

---

## Features

- **Decky / EmuDeck style dark UI**
- **Force Close Legion Space** (big red button at the top of Quick Menu)
- Performance presets + TDP slider (RyzenAdj)
- Native Legion Go resolutions (1600x1000 etc.)
- Built-in **OptiScaler** downloader
- Detects **Lossless Scaling** before launching
- Official **AMD Adrenalin 25.30.44** driver button (Lenovo package)
- Button mapping guidance (Left = open app, Right = Quick Menu)
- **One-click updater** — pulls latest files from GitHub and restarts
- Version number shown in the app

---

## Updating

Open the Quick Menu → **APP UPDATES** → **Check & Update from GitHub**

It downloads the newest `main.py` and friends from the repo and restarts automatically.

---

## Right Legion Button

The physical right Legion button cannot be captured by a normal Python app.

Map it with **PowerToys Keyboard Manager** or **AutoHotkey** so it runs:

```
"C:\path\to\your\folder\run.bat" --menu
```

That opens the app with the Quick Menu already open.

---

## Hotkeys

- `Ctrl + Shift + L` or `F1` → Toggle Quick Menu
- `Esc` → Close Quick Menu

---

Repo: https://github.com/devin12310-prog/Legion-Custom-App

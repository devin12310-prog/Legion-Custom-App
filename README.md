# Legion Custom App

Custom quick-settings app for the **first-gen Lenovo Legion Go (Ryzen Z1 Extreme)**.

Replaces the need for Legion Space for daily use, with built-in support for:

- Performance presets + TDP control (RyzenAdj)
- Display resolution / refresh rate (native Legion Go resolutions)
- **OptiScaler** (download & update directly from the app)
- Frame generation options (Lossless Scaling, AFMF, OptiFG, XeFG)
- Legion Go button mapper notes
- Force-close Legion Space (so buttons don’t conflict)
- Official AMD Adrenalin **25.30.44** driver link for Legion Go

---

## Download (one ZIP)

### Easiest way right now:

1. Go to the repository:  
   **https://github.com/devin12310-prog/Legion-Custom-App**

2. Click the green **Code** button

3. Click **Download ZIP**

4. Extract the ZIP anywhere

5. Open a terminal / PowerShell in the extracted folder and run:

```powershell
pip install -r requirements.txt
python main.py
```

That’s it. No releases page needed — the Code → Download ZIP always gives you the latest version of the whole app.

---

## Features

| Section | What it does |
|---------|--------------|
| **Performance** | Quiet / Balanced / Performance / Custom presets |
| **TDP Limit** | Slider + Apply (uses RyzenAdj if present) |
| **Display** | Legion Go native resolutions + refresh rate |
| **Scalers & Frame Gen** | Built-in OptiScaler downloader + Lossless Scaling launch |
| **Mapper & Buttons** | Recommended left/right Legion button duties |
| **Legion Space Control** | Force-close Legion Space processes |
| **Drivers & Updates** | Direct link to official Lenovo AMD 25.30.44 package |

---

## Recommended button setup

- **Left Legion button** → Launch this app  
- **Right / Top button** → Open the Quick Menu  
- Map them with **PowerToys Keyboard Manager** or **AutoHotkey** so they open this app instead of Legion Space.

Then use the red **Force Close Legion Space** button whenever the stock app is running and stealing the buttons.

---

## OptiScaler (built-in)

1. Open Quick Menu → **SCALERS & FRAME GEN**
2. Click **Download / Update OptiScaler**
3. The app pulls the latest release from the official GitHub repo into an `OptiScaler` folder
4. Copy the files into your game directory (usually rename the main DLL to `dxgi.dll`)

---

## AMD Driver 25.30.44 (Legion Go)

In the app go to **DRIVERS & UPDATES** and click the orange button.  
It opens the official Lenovo page for the package made specifically for the first-gen Legion Go.

---

## Requirements

- Windows 11
- Python 3.10+
- `pip install -r requirements.txt` (only needs `customtkinter` and optionally `psutil`)

Optional:
- `ryzenadj.exe` next to the app for real TDP control
- Lossless Scaling (Steam) for LSFG

---

## Hotkeys

- `Ctrl + Shift + L` or `F1` → Toggle Quick Menu
- `Esc` → Close Quick Menu

You can also launch with the menu already open:

```powershell
python main.py --menu
```

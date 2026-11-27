# Legion Custom v2.1.0

Right-side **Game Menu** for the Legion Go: TDP, fan, upscalers, frame gen, resolutions.

## Setup

1. Make the GitHub repo **Public**
2. Install Python + run `install.bat`
3. App force-closes Legion Space on launch so stock menu does not fight it

## Game Menu (right overlay)

Open with:
- **GAME MENU** button on the left sidebar
- **F1** or **Ctrl+Shift+L**
- `run.bat --menu` (what the Legion button helper runs)

Contains:
- Force Close Legion Space
- Performance presets + TDP + fan
- Upscaler + OptiScaler download/apply/remove
- Frame gen + Launch Lossless Scaling
- Resolution / refresh quick toggles

## Legion physical button

Stock Legion Space owns that button. This app kills Legion Space on start.

Then either:
- Press **F1**
- Or run `legion_button.ahk` (AutoHotkey) so a hotkey launches the Game Menu

True exclusive capture of the hardware Legion key needs Handheld Companion or similar; this app focuses on the menu itself.

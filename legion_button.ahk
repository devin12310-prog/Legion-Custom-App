; Legion Custom - Right Legion button helper
; 1. Install AutoHotkey v1 or v2
; 2. Force Close Legion Space first (app does this on start)
; 3. Run this script as Administrator
; 4. Press the right Legion button / or F1 to open Game Menu
;
; If the physical Legion button still does nothing after Legion Space is closed,
; use F1 or Ctrl+Shift+L inside the app, or remap in Handheld Companion.

#NoEnv
#SingleInstance Force
SendMode Input

; Path to this app's run.bat (same folder as this script)
AppDir := A_ScriptDir
RunBat := AppDir . "\run.bat"

; F1 opens Game Menu
F1::
    Run, "%RunBat%" --menu
return

; Ctrl+Shift+L also opens Game Menu
^+l::
    Run, "%RunBat%" --menu
return

; Optional: try common fallback keys some handheld tools use
; Uncomment if you find which key the Legion button emits after Space is closed:
; SC122::
;     Run, "%RunBat%" --menu
; return

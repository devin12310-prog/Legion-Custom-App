#!/usr/bin/env python3
"""Legion Custom App v2.0.0 - Multi-page Legion Space style UI"""

import customtkinter as ctk
import subprocess, os, sys, webbrowser, json, threading, time, shutil, tempfile, zipfile
from pathlib import Path
import urllib.request
from tkinter import filedialog

try:
    import psutil
except ImportError:
    psutil = None

APP_NAME = "Legion Custom"
APP_VERSION = "2.0.0"
GITHUB_REPO = "devin12310-prog/Legion-Custom-App"
GITHUB_PAGE = f"https://github.com/{GITHUB_REPO}"
GITHUB_ZIP = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"

APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "config.json"
OPTISCALER_DIR = APP_DIR / "OptiScaler"
APPLIED_LOG = APP_DIR / "applied_games.json"

LENOVO_AMD_URL = "https://support.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1/downloads/ds565497-amd-graphics-driver-for-windows-11-64-bit-legion-go-8apu1"

LEGION_PROCS = [
    "LegionSpace.exe", "LSDaemon.exe", "LegionSettingMenu.exe",
    "LegionGameWidget.exe", "LegionGameWidget_Sub.exe",
    "LegionSpaceComponent.exe", "LegionSpaceToast.exe",
]

DEFAULT = {
    "tdp": 25, "preset": "Balanced", "fan": "Smart",
    "scaler": "None", "fg": "Off", "res": "1600x1000", "hz": 144,
    "dll": "dxgi.dll",
}

# Legion Space-like palette
BG = "#0a0e14"
SIDE = "#0f141c"
CARD = "#151c28"
CARD2 = "#1a2332"
ACCENT = "#00d4aa"
ACCENT2 = "#00b894"
BLUE = "#3d8bfd"
RED = "#ff4757"
ORANGE = "#ffa502"
TEXT = "#e8eef7"
DIM = "#8b9bb4"
MUTED = "#4a5568"
PILL = "#1e2836"

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1600x1000")
        self.minsize(1280, 800)
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))

        self.cfg = self._load(CONFIG_FILE, DEFAULT)
        self.applied = self._load(APPLIED_LOG, {})
        self.busy = False
        self.page = "home"
        self.pages = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar()
        self._content()
        self._build_pages()
        self.show("home")

        self.bind("<F1>", lambda e: self.show("perf"))
        self.bind("<Escape>", lambda e: self.show("home"))
        if "--menu" in sys.argv:
            self.after(200, lambda: self.show("perf"))

        self.after(400, self.refresh_games)
        self.after(600, self.refresh_tools)
        self.after(1000, self._stats)

    def _load(self, path, default):
        if Path(path).exists():
            try:
                return {**default, **json.loads(Path(path).read_text())}
            except Exception:
                pass
        return default.copy() if isinstance(default, dict) else default

    def _save(self, path, data):
        try:
            Path(path).write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def setc(self, k, v):
        self.cfg[k] = v
        self._save(CONFIG_FILE, self.cfg)

    # ========== SIDEBAR (Legion Space style icons) ==========
    def _sidebar(self):
        side = ctk.CTkFrame(self, width=88, fg_color=SIDE, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)

        ctk.CTkLabel(side, text="LC", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=ACCENT).pack(pady=(24, 28))

        self.nav_btns = {}
        items = [
            ("home", "Games", "🎮"),
            ("perf", "Perf", "⚡"),
            ("display", "Display", "🖥"),
            ("scaler", "Scaler", "🔍"),
            ("fg", "FrameGen", "⧖"),
            ("drivers", "Drivers", "🛠"),
            ("settings", "Settings", "⚙"),
        ]
        for key, label, icon in items:
            f = ctk.CTkFrame(side, fg_color="transparent")
            f.pack(fill="x", pady=4)
            b = ctk.CTkButton(
                f, text=f"{icon}\n{label}", width=72, height=64,
                font=ctk.CTkFont(size=11), fg_color="transparent",
                hover_color=CARD, text_color=DIM,
                command=lambda k=key: self.show(k)
            )
            b.pack()
            self.nav_btns[key] = b

        ctk.CTkLabel(side, text=f"v{APP_VERSION}", font=ctk.CTkFont(size=10),
                     text_color=MUTED).pack(side="bottom", pady=16)

    def _content(self):
        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def show(self, key):
        self.page = key
        for k, f in self.pages.items():
            if k == key:
                f.grid(row=0, column=0, sticky="nsew")
            else:
                f.grid_remove()
        for k, b in self.nav_btns.items():
            if k == key:
                b.configure(fg_color=CARD, text_color=ACCENT)
            else:
                b.configure(fg_color="transparent", text_color=DIM)

    def _page(self):
        f = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(1, weight=1)
        return f

    def _title(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))

    def _scroll(self, parent):
        s = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        s.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        s.grid_columnconfigure(0, weight=1)
        return s

    def _card(self, parent, **kw):
        c = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16, **kw)
        c.pack(fill="x", pady=8, padx=4)
        return c

    def _h(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=DIM).pack(anchor="w", padx=20, pady=(16, 8))

    # ========== BUILD ALL PAGES ==========
    def _build_pages(self):
        self._page_home()
        self._page_perf()
        self._page_display()
        self._page_scaler()
        self._page_fg()
        self._page_drivers()
        self._page_settings()

    # ----- HOME / GAMES -----
    def _page_home(self):
        p = self._page()
        self.pages["home"] = p
        top = ctk.CTkFrame(p, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        ctk.CTkLabel(top, text="Games", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(top, text="Refresh", width=110, height=36, fg_color=CARD,
                      command=self.refresh_games).pack(side="right")

        self.games_frame = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.games_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.games_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Quick force close bar
        bar = ctk.CTkFrame(p, fg_color=CARD, height=56, corner_radius=0)
        bar.grid(row=2, column=0, sticky="ew")
        ctk.CTkButton(bar, text="Force Close Legion Space", height=40,
                      fg_color=RED, hover_color="#e03e4e",
                      font=ctk.CTkFont(weight="bold"),
                      command=self.force_close).pack(side="left", padx=16, pady=8)
        self.fc_lbl = ctk.CTkLabel(bar, text="", text_color=DIM)
        self.fc_lbl.pack(side="left", padx=8)

    # ----- PERFORMANCE -----
    def _page_perf(self):
        p = self._page()
        self.pages["perf"] = p
        self._title(p, "Performance")
        s = self._scroll(p)

        # Recommended presets
        self._h(s, "RECOMMENDED PRESETS")
        c = self._card(s)
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=16)
        presets = [
            ("Quiet", "15W \u00b7 Cool & quiet", 15),
            ("Balanced", "25W \u00b7 Best everyday", 25),
            ("Performance", "35W \u00b7 Max power", 35),
        ]
        self.preset_btns = {}
        for key, desc, tdp in presets:
            f = ctk.CTkFrame(row, fg_color=PILL, corner_radius=12)
            f.pack(side="left", expand=True, fill="both", padx=6)
            b = ctk.CTkButton(f, text=key, height=40, font=ctk.CTkFont(size=15, weight="bold"),
                              fg_color="transparent", text_color=TEXT,
                              command=lambda k=key, t=tdp: self.apply_preset(k, t))
            b.pack(fill="x", padx=8, pady=(12, 0))
            ctk.CTkLabel(f, text=desc, text_color=DIM, font=ctk.CTkFont(size=12)).pack(pady=(0, 12))
            self.preset_btns[key] = f

        # Live stats
        self._h(s, "LIVE STATS")
        c = self._card(s)
        stats = ctk.CTkFrame(c, fg_color="transparent")
        stats.pack(fill="x", padx=16, pady=16)
        self.stat = {}
        for k, n in [("cpu", "CPU"), ("gpu", "GPU"), ("vram", "VRAM"), ("ram", "RAM")]:
            box = ctk.CTkFrame(stats, fg_color=PILL, corner_radius=12)
            box.pack(side="left", expand=True, fill="x", padx=6)
            self.stat[k] = ctk.CTkLabel(box, text="--%", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT)
            self.stat[k].pack(pady=(16, 0))
            ctk.CTkLabel(box, text=n, text_color=DIM).pack(pady=(0, 16))

        # TDP
        self._h(s, "TDP LIMIT")
        c = self._card(s)
        self.tdp_lbl = ctk.CTkLabel(c, text=f"{self.cfg.get('tdp',25)} W",
                                    font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT)
        self.tdp_lbl.pack(pady=(20, 8))
        self.tdp_slider = ctk.CTkSlider(c, from_=8, to=40, number_of_steps=32,
                                        progress_color=ACCENT, button_color=ACCENT,
                                        command=self.on_tdp)
        self.tdp_slider.set(self.cfg.get("tdp", 25))
        self.tdp_slider.pack(fill="x", padx=24, pady=8)
        ctk.CTkButton(c, text="Apply TDP", height=48, fg_color=ACCENT, hover_color=ACCENT2,
                      text_color="#000", font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.apply_tdp).pack(fill="x", padx=20, pady=(8, 20))

        # Fan
        self._h(s, "FAN")
        c = self._card(s)
        frow = ctk.CTkFrame(c, fg_color="transparent")
        frow.pack(fill="x", padx=16, pady=16)
        self.fan_btns = {}
        for key, label in [("Smart", "Smart (Recommended)"), ("Full", "Full Speed")]:
            b = ctk.CTkButton(frow, text=label, height=48, font=ctk.CTkFont(size=14, weight="bold"),
                              fg_color=PILL, command=lambda k=key: self.set_fan(k))
            b.pack(side="left", expand=True, fill="x", padx=6)
            self.fan_btns[key] = b
        self._hl_fan()

    # ----- DISPLAY -----
    def _page_display(self):
        p = self._page()
        self.pages["display"] = p
        self._title(p, "Display")
        s = self._scroll(p)

        self._h(s, "RESOLUTION  (Legion Go native)")
        c = self._card(s)
        rrow = ctk.CTkFrame(c, fg_color="transparent")
        rrow.pack(fill="x", padx=16, pady=16)
        self.res_btns = {}
        for res, note in [("1280x800", "Light"), ("1600x1000", "Recommended"), ("1920x1200", "Sharp")]:
            f = ctk.CTkFrame(rrow, fg_color=PILL, corner_radius=12)
            f.pack(side="left", expand=True, fill="both", padx=6)
            b = ctk.CTkButton(f, text=res, height=40, font=ctk.CTkFont(size=14, weight="bold"),
                              fg_color="transparent", command=lambda r=res: self.set_res(r))
            b.pack(fill="x", pady=(12, 0), padx=8)
            ctk.CTkLabel(f, text=note, text_color=DIM).pack(pady=(0, 12))
            self.res_btns[res] = f
        self._hl_res()

        self._h(s, "REFRESH RATE")
        c = self._card(s)
        hrow = ctk.CTkFrame(c, fg_color="transparent")
        hrow.pack(fill="x", padx=16, pady=16)
        self.hz_btns = {}
        for hz, note in [(60, "Battery"), (144, "Recommended")]:
            f = ctk.CTkFrame(hrow, fg_color=PILL, corner_radius=12)
            f.pack(side="left", expand=True, fill="both", padx=6)
            b = ctk.CTkButton(f, text=f"{hz} Hz", height=44, font=ctk.CTkFont(size=16, weight="bold"),
                              fg_color="transparent", command=lambda h=hz: self.set_hz(h))
            b.pack(fill="x", pady=(12, 0), padx=8)
            ctk.CTkLabel(f, text=note, text_color=DIM).pack(pady=(0, 12))
            self.hz_btns[hz] = f
        self._hl_hz()

    # ----- SCALER -----
    def _page_scaler(self):
        p = self._page()
        self.pages["scaler"] = p
        self._title(p, "Upscaler")
        s = self._scroll(p)

        self._h(s, "SELECT UPSCALER")
        c = self._card(s)
        self.scaler_var = ctk.StringVar(value=self.cfg.get("scaler", "None"))
        ctk.CTkOptionMenu(
            c, values=["None", "FSR 2 / 3 / 4", "XeSS", "OptiScaler (Auto)", "DLSS Spoof"],
            variable=self.scaler_var, command=lambda v: self.setc("scaler", v),
            height=48, font=ctk.CTkFont(size=15), fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=20, pady=16)

        self._h(s, "OPTISCALER")
        c = self._card(s)
        self.opti_status = ctk.CTkLabel(c, text="Checking...", text_color=DIM,
                                        font=ctk.CTkFont(size=14))
        self.opti_status.pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(c, text="DLL name", text_color=DIM).pack(anchor="w", padx=20)
        self.dll_var = ctk.StringVar(value=self.cfg.get("dll", "dxgi.dll"))
        ctk.CTkOptionMenu(
            c, values=["dxgi.dll", "winmm.dll", "version.dll", "dbghelp.dll"],
            variable=self.dll_var, command=lambda v: self.setc("dll", v),
            height=40, fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=20, pady=(4, 12))

        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.opti_dl = ctk.CTkButton(row, text="Download / Update OptiScaler", height=48,
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     fg_color=ACCENT, hover_color=ACCENT2, text_color="#000",
                                     command=self.download_opti)
        self.opti_dl.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text="Open Folder", width=120, height=48, fg_color=PILL,
                      command=self.open_opti).pack(side="left")

        row2 = ctk.CTkFrame(c, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkButton(row2, text="Apply to Game Folder", height=48,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=BLUE, command=self.apply_opti).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row2, text="Remove from Folder", height=48,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=RED, command=self.remove_opti).pack(side="left", expand=True, fill="x")

        self.apply_lbl = ctk.CTkLabel(c, text="Apply copies OptiScaler into a game so it loads on launch",
                                      text_color=MUTED, font=ctk.CTkFont(size=12))
        self.apply_lbl.pack(anchor="w", padx=20, pady=(4, 16))

        self._h(s, "RECOMMENDED")
        c = self._card(s)
        ctk.CTkLabel(c, text="Most Legion Go games: OptiScaler + FSR or XeSS\n"
                             "DLL: try dxgi.dll first, then winmm.dll if it fails\n"
                             "Remove when you want stock game behavior",
                     text_color=TEXT, font=ctk.CTkFont(size=14), justify="left").pack(
            anchor="w", padx=20, pady=16)

    # ----- FRAME GEN -----
    def _page_fg(self):
        p = self._page()
        self.pages["fg"] = p
        self._title(p, "Frame Generation")
        s = self._scroll(p)

        self._h(s, "SELECT METHOD")
        c = self._card(s)
        self.fg_var = ctk.StringVar(value=self.cfg.get("fg", "Off"))
        ctk.CTkOptionMenu(
            c, values=["Off", "Lossless Scaling (LSFG)", "AMD AFMF", "OptiFG", "XeFG"],
            variable=self.fg_var, command=self.on_fg,
            height=48, font=ctk.CTkFont(size=15), fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=20, pady=16)

        self.fg_status = ctk.CTkLabel(c, text="", text_color=DIM, font=ctk.CTkFont(size=13))
        self.fg_status.pack(anchor="w", padx=20, pady=(0, 8))

        self.ls_btn = ctk.CTkButton(c, text="Launch Lossless Scaling", height=52,
                                    font=ctk.CTkFont(size=15, weight="bold"),
                                    fg_color=BLUE, command=self.launch_ls)
        self.ls_btn.pack(fill="x", padx=20, pady=(0, 16))

        self._h(s, "BEST OPTIONS FOR LEGION GO")
        c = self._card(s)
        tips = (
            "1. Lossless Scaling (LSFG) \u2014 best general FG, launch from here\n"
            "2. AMD AFMF \u2014 enable in Adrenalin, lowest overhead\n"
            "3. OptiFG / XeFG \u2014 after applying OptiScaler to the game\n\n"
            "Tip: Leave FG Off when you want max battery / lowest latency"
        )
        ctk.CTkLabel(c, text=tips, text_color=TEXT, font=ctk.CTkFont(size=14),
                     justify="left").pack(anchor="w", padx=20, pady=16)

    # ----- DRIVERS -----
    def _page_drivers(self):
        p = self._page()
        self.pages["drivers"] = p
        self._title(p, "Drivers")
        s = self._scroll(p)

        self._h(s, "OFFICIAL LEGION GO DRIVER")
        c = self._card(s)
        ctk.CTkLabel(c, text="AMD Adrenalin 25.30.44", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(c, text="Lenovo package for Z1 Extreme \u2014 recommended",
                     text_color=DIM).pack(anchor="w", padx=20, pady=(0, 12))
        ctk.CTkButton(c, text="Download AMD 25.30.44", height=52,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=ORANGE, hover_color="#e69500",
                      command=lambda: webbrowser.open(LENOVO_AMD_URL)).pack(fill="x", padx=20, pady=(0, 16))

        self._h(s, "LEGION SPACE")
        c = self._card(s)
        ctk.CTkButton(c, text="Force Close Legion Space", height=52,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=RED, command=self.force_close).pack(fill="x", padx=20, pady=16)
        self.fc_lbl2 = ctk.CTkLabel(c, text="Stops button conflicts with this app", text_color=DIM)
        self.fc_lbl2.pack(anchor="w", padx=20, pady=(0, 12))

    # ----- SETTINGS -----
    def _page_settings(self):
        p = self._page()
        self.pages["settings"] = p
        self._title(p, "Settings")
        s = self._scroll(p)

        self._h(s, "APP UPDATES")
        c = self._card(s)
        self.upd_lbl = ctk.CTkLabel(c, text=f"Current version: {APP_VERSION}",
                                    text_color=DIM, font=ctk.CTkFont(size=14))
        self.upd_lbl.pack(anchor="w", padx=20, pady=(16, 8))
        self.upd_btn = ctk.CTkButton(c, text="Check & Update from GitHub", height=52,
                                     font=ctk.CTkFont(size=15, weight="bold"),
                                     fg_color=ACCENT, hover_color=ACCENT2, text_color="#000",
                                     command=self.do_update)
        self.upd_btn.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkButton(c, text="Open GitHub Page", height=44, fg_color=PILL,
                      command=lambda: webbrowser.open(GITHUB_PAGE)).pack(fill="x", padx=20, pady=(0, 16))

        self._h(s, "RIGHT LEGION BUTTON")
        c = self._card(s)
        msg = (
            "This app cannot capture the physical Legion button by itself.\n\n"
            "Map it with PowerToys Keyboard Manager or AutoHotkey to run:\n\n"
            f"  {APP_DIR / 'run.bat'} --menu\n\n"
            "That opens the Performance page (Quick Menu equivalent)."
        )
        ctk.CTkLabel(c, text=msg, text_color=TEXT, font=ctk.CTkFont(size=13),
                     justify="left").pack(anchor="w", padx=20, pady=16)

        self._h(s, "HOTKEYS")
        c = self._card(s)
        ctk.CTkLabel(c, text="F1  \u2192 Performance page\nEsc \u2192 Games home",
                     text_color=TEXT, font=ctk.CTkFont(size=14), justify="left").pack(
            anchor="w", padx=20, pady=16)

    # ========== ACTIONS ==========
    def apply_preset(self, key, tdp):
        self.setc("preset", key)
        self.setc("tdp", tdp)
        self.tdp_slider.set(tdp)
        self.tdp_lbl.configure(text=f"{tdp} W")
        for k, f in self.preset_btns.items():
            f.configure(fg_color=ACCENT if k == key else PILL)

    def on_tdp(self, v):
        val = int(float(v))
        self.tdp_lbl.configure(text=f"{val} W")
        self.setc("tdp", val)
        self.setc("preset", "Custom")

    def set_fan(self, key):
        self.setc("fan", key)
        self._hl_fan()

    def _hl_fan(self):
        cur = self.cfg.get("fan", "Smart")
        for k, b in self.fan_btns.items():
            b.configure(fg_color=ACCENT if k == cur else PILL,
                        text_color="#000" if k == cur else TEXT)

    def set_res(self, r):
        self.setc("res", r)
        self._hl_res()

    def _hl_res(self):
        cur = self.cfg.get("res", "1600x1000")
        for k, f in self.res_btns.items():
            f.configure(fg_color=ACCENT if k == cur else PILL)

    def set_hz(self, h):
        self.setc("hz", h)
        self._hl_hz()

    def _hl_hz(self):
        cur = int(self.cfg.get("hz", 144))
        for k, f in self.hz_btns.items():
            f.configure(fg_color=ACCENT if k == cur else PILL)

    def on_fg(self, v):
        self.setc("fg", v)
        if v == "Lossless Scaling (LSFG)":
            self.fg_status.configure(text="Launch Lossless Scaling below, then enable FG in its overlay", text_color=ACCENT)
        elif v == "AMD AFMF":
            self.fg_status.configure(text="Turn on AFMF inside AMD Adrenalin \u2192 Graphics", text_color=ORANGE)
        elif v in ("OptiFG", "XeFG"):
            self.fg_status.configure(text="Apply OptiScaler to the game first (Scaler page)", text_color=ORANGE)
        else:
            self.fg_status.configure(text="Frame gen off \u2014 best for battery/latency", text_color=DIM)

    def force_close(self):
        killed = []
        if psutil:
            for p in psutil.process_iter(["name"]):
                try:
                    n = p.info["name"]
                    if n and n.lower() in [x.lower() for x in LEGION_PROCS]:
                        p.kill(); killed.append(n)
                except Exception:
                    pass
        else:
            for name in LEGION_PROCS:
                try:
                    r = subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True,
                                       creationflags=0x08000000 if sys.platform == "win32" else 0)
                    if r.returncode == 0:
                        killed.append(name)
                except Exception:
                    pass
        msg = f"Closed: {', '.join(sorted(set(killed)))}" if killed else "No Legion Space processes found"
        self.fc_lbl.configure(text=msg, text_color=ACCENT if killed else DIM)
        if hasattr(self, "fc_lbl2"):
            self.fc_lbl2.configure(text=msg, text_color=ACCENT if killed else DIM)

    def _stats(self):
        if psutil:
            try:
                self.stat["cpu"].configure(text=f"{psutil.cpu_percent(interval=None):.0f}%")
                self.stat["ram"].configure(text=f"{psutil.virtual_memory().percent:.0f}%")
            except Exception:
                pass
        self.after(2000, self._stats)

    def apply_tdp(self):
        tdp = int(self.cfg.get("tdp", 25))
        for c in [APP_DIR / "ryzenadj.exe", Path("C:/tools/ryzenadj/ryzenadj.exe")]:
            if c.exists():
                try:
                    subprocess.Popen([str(c), f"--stapm-limit={tdp*1000}",
                                      f"--fast-limit={tdp*1000}", f"--slow-limit={tdp*1000}"],
                                     creationflags=0x08000000 if sys.platform == "win32" else 0)
                except Exception:
                    pass
                return

    # OptiScaler
    def refresh_tools(self):
        if OPTISCALER_DIR.exists() and any(OPTISCALER_DIR.iterdir()):
            self.opti_status.configure(text="OptiScaler: Installed \u2014 ready to apply", text_color=ACCENT)
            self.opti_dl.configure(text="Update OptiScaler")
        else:
            self.opti_status.configure(text="OptiScaler: Not installed", text_color=DIM)
            self.opti_dl.configure(text="Download OptiScaler")
        ls = self.find_ls()
        if ls:
            self.fg_status.configure(text="Lossless Scaling: Found", text_color=ACCENT)
        else:
            self.fg_status.configure(text="Lossless Scaling: Not found (install on Steam)", text_color=DIM)

    def download_opti(self):
        if self.busy: return
        self.busy = True
        self.opti_dl.configure(text="Downloading...", state="disabled")
        self.opti_status.configure(text="Downloading from GitHub...", text_color=ORANGE)

        def work():
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/optiscaler/OptiScaler/releases/latest",
                    headers={"User-Agent": "Legion-Custom-App"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode())
                tag = data.get("tag_name", "?")
                url = next((a["browser_download_url"] for a in data.get("assets", [])
                            if a["name"].lower().endswith(".zip")), data.get("zipball_url"))
                with tempfile.TemporaryDirectory() as tmp:
                    zp = Path(tmp) / "o.zip"
                    urllib.request.urlretrieve(url, zp)
                    out = Path(tmp) / "e"; out.mkdir()
                    with zipfile.ZipFile(zp) as z: z.extractall(out)
                    if OPTISCALER_DIR.exists(): shutil.rmtree(OPTISCALER_DIR)
                    OPTISCALER_DIR.mkdir()
                    items = list(out.iterdir())
                    src = items[0] if len(items) == 1 and items[0].is_dir() else out
                    for it in src.iterdir():
                        d = OPTISCALER_DIR / it.name
                        if it.is_dir(): shutil.copytree(it, d)
                        else: shutil.copy2(it, d)
                self.after(0, lambda: self.opti_status.configure(
                    text=f"Installed {tag} \u2014 ready to apply", text_color=ACCENT))
            except Exception as e:
                self.after(0, lambda: self.opti_status.configure(text=f"Failed: {e}", text_color=RED))
            finally:
                self.busy = False
                self.after(0, lambda: self.opti_dl.configure(state="normal"))
                self.after(0, self.refresh_tools)

        threading.Thread(target=work, daemon=True).start()

    def open_opti(self):
        OPTISCALER_DIR.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OPTISCALER_DIR)

    def apply_opti(self):
        if not OPTISCALER_DIR.exists() or not any(OPTISCALER_DIR.iterdir()):
            self.apply_lbl.configure(text="Download OptiScaler first", text_color=RED)
            return
        folder = filedialog.askdirectory(title="Select game folder")
        if not folder:
            return
        folder = Path(folder)
        dll = self.dll_var.get() or "dxgi.dll"
        try:
            target = folder / dll
            bak = folder / (dll + ".legionbak")
            if target.exists() and not bak.exists():
                shutil.copy2(target, bak)
            for item in OPTISCALER_DIR.iterdir():
                dest = folder / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    if dest.exists(): shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            for cand in ["OptiScaler.dll", "dxgi.dll", "winmm.dll"]:
                p = OPTISCALER_DIR / cand
                if p.exists() and p.name.lower() != dll.lower():
                    src = folder / p.name
                    if src.exists():
                        shutil.copy2(src, folder / dll)
                    break
            self.applied[str(folder.resolve())] = {"dll": dll, "time": time.strftime("%Y-%m-%d %H:%M")}
            self._save(APPLIED_LOG, self.applied)
            self.apply_lbl.configure(text=f"Applied to {folder.name} ({dll})", text_color=ACCENT)
            self.refresh_games()
        except Exception as e:
            self.apply_lbl.configure(text=f"Failed: {e}", text_color=RED)

    def remove_opti(self):
        folder = filedialog.askdirectory(title="Select game folder to clean")
        if not folder:
            return
        folder = Path(folder)
        try:
            for dll in ["dxgi.dll", "winmm.dll", "version.dll", "dbghelp.dll"]:
                bak = folder / (dll + ".legionbak")
                if bak.exists():
                    shutil.copy2(bak, folder / dll)
                    bak.unlink()
            for name in ["OptiScaler.dll", "OptiScaler.ini", "nvngx.dll", "libxess.dll"]:
                p = folder / name
                if p.exists():
                    p.unlink()
            key = str(folder.resolve())
            if key in self.applied:
                del self.applied[key]
                self._save(APPLIED_LOG, self.applied)
            self.apply_lbl.configure(text=f"Removed from {folder.name}", text_color=ACCENT)
            self.refresh_games()
        except Exception as e:
            self.apply_lbl.configure(text=f"Failed: {e}", text_color=RED)

    def find_ls(self):
        cands = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
        ]
        for d in "CDEF":
            cands.append(Path(f"{d}:/SteamLibrary/steamapps/common/Lossless Scaling/LosslessScaling.exe"))
        for p in cands:
            if p.exists():
                return p
        return None

    def launch_ls(self):
        p = self.find_ls()
        if p:
            subprocess.Popen([str(p)])
            self.fg_status.configure(text="Lossless Scaling launched", text_color=ACCENT)
        else:
            try:
                subprocess.Popen(["cmd", "/c", "start", "steam://rungameid/993090"], shell=True)
            except Exception:
                self.fg_status.configure(text="Install Lossless Scaling from Steam", text_color=RED)

    def do_update(self):
        if self.busy: return
        self.busy = True
        self.upd_btn.configure(state="disabled", text="Updating...")
        self.upd_lbl.configure(text="Downloading... (repo must be Public)", text_color=ORANGE)

        def work():
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    zp = Path(tmp) / "repo.zip"
                    req = urllib.request.Request(GITHUB_ZIP, headers={"User-Agent": "Legion-Custom-App"})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        zp.write_bytes(r.read())
                    extract = Path(tmp) / "out"; extract.mkdir()
                    with zipfile.ZipFile(zp) as z:
                        z.extractall(extract)
                    inner = next(extract.iterdir())
                    updated = []
                    for fname in ["main.py", "requirements.txt", "README.md", "install.bat", "run.bat"]:
                        src = inner / fname
                        if src.exists():
                            tmp_dst = APP_DIR / (fname + ".new")
                            shutil.copy2(src, tmp_dst)
                            tmp_dst.replace(APP_DIR / fname)
                            updated.append(fname)
                    if updated:
                        self.after(0, lambda: self.upd_lbl.configure(
                            text=f"Updated {len(updated)} files \u2014 restarting...", text_color=ACCENT))
                        time.sleep(1.5)
                        subprocess.Popen([sys.executable, str(APP_DIR / "main.py")] + sys.argv[1:], cwd=str(APP_DIR))
                        self.after(0, self.destroy)
                    else:
                        self.after(0, lambda: self.upd_lbl.configure(text="Already up to date", text_color=ACCENT))
            except Exception as e:
                err = str(e)
                if "404" in err:
                    err = "404 Not Found \u2014 make the GitHub repo PUBLIC (Settings \u2192 Danger Zone)"
                self.after(0, lambda: self.upd_lbl.configure(text=f"Failed: {err}", text_color=RED))
            finally:
                self.busy = False
                self.after(0, lambda: self.upd_btn.configure(state="normal", text="Check & Update from GitHub"))

        threading.Thread(target=work, daemon=True).start()

    def refresh_games(self):
        for w in self.games_frame.winfo_children():
            w.destroy()
        games = self.scan_games()
        if not games:
            ctk.CTkLabel(self.games_frame, text="No Steam games found", text_color=MUTED,
                         font=ctk.CTkFont(size=16)).grid(row=0, column=0, columnspan=4, pady=80)
            return
        for i, g in enumerate(games):
            r, c = divmod(i, 4)
            card = ctk.CTkFrame(self.games_frame, width=240, height=150, corner_radius=14, fg_color=CARD)
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            applied = str(Path(g["path"]).parent.resolve()) in self.applied
            name = g["name"][:22] + ("  \u2713" if applied else "")
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=ACCENT if applied else TEXT, wraplength=210).pack(pady=(20, 10), padx=10)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack()
            if Path(g["path"]).exists():
                ctk.CTkButton(row, text="Play", width=90, height=34,
                              fg_color=ACCENT, hover_color=ACCENT2, text_color="#000",
                              command=lambda p=g["path"]: subprocess.Popen([p], cwd=str(Path(p).parent))).pack(side="left", padx=4)

    def scan_games(self):
        found = []
        bases = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/steamapps/common",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam/steamapps/common",
        ]
        for d in "CDEF":
            bases.append(Path(f"{d}:/SteamLibrary/steamapps/common"))
        for base in bases:
            if not base.exists():
                continue
            for gdir in base.iterdir():
                if not gdir.is_dir():
                    continue
                exes = list(gdir.glob("*.exe"))
                if not exes:
                    continue
                main = next((e for e in exes if gdir.name.lower() in e.stem.lower()), exes[0])
                found.append({"name": gdir.name, "path": str(main)})
        return list({g["name"]: g for g in found}.values())[:48]


if __name__ == "__main__":
    App().mainloop()

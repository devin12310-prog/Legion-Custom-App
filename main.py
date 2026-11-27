#!/usr/bin/env python3
"""Legion Custom v2.1.0 - Gaming right-menu overlay for Legion Go"""

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
APP_VERSION = "2.1.0"
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
    "scaler": "None", "fg": "Off", "res": "1600x1000", "hz": 144, "dll": "dxgi.dll",
}

BG, SIDE, CARD, PILL = "#0a0e14", "#0f141c", "#151c28", "#1e2836"
ACCENT, ACCENT2, BLUE, RED, ORANGE = "#00d4aa", "#00b894", "#3d8bfd", "#ff4757", "#ffa502"
TEXT, DIM, MUTED = "#e8eef7", "#8b9bb4", "#4a5568"

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1600x1000")
        self.minsize(1280, 800)
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)
        self.after(400, lambda: self.attributes("-topmost", False))

        self.cfg = self._load(CONFIG_FILE, DEFAULT)
        self.applied = self._load(APPLIED_LOG, {})
        self.busy = False
        self.game_menu_open = False
        self.pages = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar()
        self._main()
        self._game_menu()  # right overlay
        self._build_pages()
        self.show("home")

        # Hotkeys that open the RIGHT gaming menu
        self.bind("<F1>", lambda e: self.toggle_game_menu())
        self.bind("<Control-Shift-L>", lambda e: self.toggle_game_menu())
        self.bind("<Escape>", lambda e: self.close_game_menu())

        # --menu opens directly into gaming menu (for Legion button helper)
        if "--menu" in sys.argv:
            self.after(200, self.open_game_menu)

        self.after(300, self.refresh_games)
        self.after(500, self.refresh_tools)
        self.after(800, self._stats)

        # Kill Legion Space on start so it doesn't steal the button
        self.after(100, self.force_close)

    def _load(self, path, default):
        p = Path(path)
        if p.exists():
            try:
                return {**default, **json.loads(p.read_text())} if isinstance(default, dict) else json.loads(p.read_text())
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

    # ===== LEFT SIDEBAR =====
    def _sidebar(self):
        side = ctk.CTkFrame(self, width=90, fg_color=SIDE, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="LC", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=ACCENT).pack(pady=(22, 20))

        self.nav = {}
        for key, label in [("home", "Games"), ("library", "Tools"), ("drivers", "Drivers"), ("settings", "Settings")]:
            b = ctk.CTkButton(side, text=label, width=78, height=56,
                              font=ctk.CTkFont(size=12), fg_color="transparent",
                              hover_color=CARD, text_color=DIM,
                              command=lambda k=key: self.show(k))
            b.pack(pady=4)
            self.nav[key] = b

        # Big button to open gaming menu
        ctk.CTkButton(side, text="GAME\nMENU", width=78, height=70,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=ACCENT, hover_color=ACCENT2, text_color="#000",
                      command=self.toggle_game_menu).pack(side="bottom", pady=20)

    def _main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

    def show(self, key):
        for k, f in self.pages.items():
            f.grid_remove() if k != key else f.grid(row=0, column=0, sticky="nsew")
        for k, b in self.nav.items():
            b.configure(fg_color=CARD if k == key else "transparent",
                        text_color=ACCENT if k == key else DIM)

    # ===== RIGHT GAME MENU (the important overlay) =====
    def _game_menu(self):
        self.gmenu = ctk.CTkFrame(self, width=440, fg_color=SIDE, corner_radius=0)
        self.gmenu.grid(row=0, column=2, sticky="nsew")
        self.gmenu.grid_propagate(False)
        self.gmenu.grid_remove()

        # Header
        hdr = ctk.CTkFrame(self.gmenu, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(18, 6))
        ctk.CTkLabel(hdr, text="GAME MENU", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="✕", width=40, height=40, fg_color="transparent",
                      hover_color=CARD, command=self.close_game_menu).pack(side="right")

        self.gms = ctk.CTkScrollableFrame(self.gmenu, fg_color="transparent")
        self.gms.pack(fill="both", expand=True, padx=12, pady=4)

        # --- Force close ---
        self._gm_sec("LEGION SPACE")
        c = self._gm_card()
        ctk.CTkButton(c, text="FORCE CLOSE LEGION SPACE", height=50,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=RED, command=self.force_close).pack(fill="x", padx=14, pady=(14, 6))
        self.fc_lbl = ctk.CTkLabel(c, text="Closes stock menu so this one owns the button",
                                   text_color=DIM, font=ctk.CTkFont(size=12))
        self.fc_lbl.pack(anchor="w", padx=14, pady=(0, 14))

        # --- Performance presets ---
        self._gm_sec("PERFORMANCE")
        c = self._gm_card()
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=14)
        self.preset_btns = {}
        for key, tdp in [("Quiet", 15), ("Balanced", 25), ("Perf", 35)]:
            b = ctk.CTkButton(row, text=f"{key}\n{tdp}W", height=64,
                              font=ctk.CTkFont(size=13, weight="bold"),
                              fg_color=PILL, command=lambda k=key, t=tdp: self.apply_preset(k, t))
            b.pack(side="left", expand=True, fill="x", padx=4)
            self.preset_btns[key] = b

        # Stats
        stats = ctk.CTkFrame(c, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=(0, 14))
        self.stat = {}
        for k, n in [("cpu", "CPU"), ("ram", "RAM")]:
            box = ctk.CTkFrame(stats, fg_color=PILL, corner_radius=12)
            box.pack(side="left", expand=True, fill="x", padx=4)
            self.stat[k] = ctk.CTkLabel(box, text="--%", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT)
            self.stat[k].pack(pady=(12, 0))
            ctk.CTkLabel(box, text=n, text_color=DIM).pack(pady=(0, 12))

        # TDP
        self._gm_sec("TDP")
        c = self._gm_card()
        self.tdp_lbl = ctk.CTkLabel(c, text=f"{self.cfg.get('tdp',25)} W",
                                    font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT)
        self.tdp_lbl.pack(pady=(16, 4))
        self.tdp_slider = ctk.CTkSlider(c, from_=8, to=40, number_of_steps=32,
                                        progress_color=ACCENT, button_color=ACCENT, command=self.on_tdp)
        self.tdp_slider.set(self.cfg.get("tdp", 25))
        self.tdp_slider.pack(fill="x", padx=18, pady=6)
        ctk.CTkButton(c, text="Apply TDP", height=46, fg_color=ACCENT, hover_color=ACCENT2,
                      text_color="#000", font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.apply_tdp).pack(fill="x", padx=14, pady=(6, 16))

        # Fan
        self._gm_sec("FAN")
        c = self._gm_card()
        frow = ctk.CTkFrame(c, fg_color="transparent")
        frow.pack(fill="x", padx=12, pady=14)
        self.fan_btns = {}
        for key, label in [("Smart", "Smart"), ("Full", "Full Speed")]:
            b = ctk.CTkButton(frow, text=label, height=48, font=ctk.CTkFont(size=14, weight="bold"),
                              fg_color=PILL, command=lambda k=key: self.set_fan(k))
            b.pack(side="left", expand=True, fill="x", padx=4)
            self.fan_btns[key] = b
        self._hl_fan()

        # Scaler
        self._gm_sec("UPSCALER")
        c = self._gm_card()
        self.scaler_var = ctk.StringVar(value=self.cfg.get("scaler", "None"))
        ctk.CTkOptionMenu(
            c, values=["None", "FSR 2/3/4", "XeSS", "OptiScaler", "DLSS Spoof"],
            variable=self.scaler_var, command=lambda v: self.setc("scaler", v),
            height=46, font=ctk.CTkFont(size=14), fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(14, 8))

        self.opti_status = ctk.CTkLabel(c, text="OptiScaler: ...", text_color=DIM)
        self.opti_status.pack(anchor="w", padx=14, pady=(0, 6))

        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 8))
        self.opti_dl = ctk.CTkButton(row, text="Download", height=44, fg_color=ACCENT,
                                     text_color="#000", command=self.download_opti)
        self.opti_dl.pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(row, text="Apply to Game", height=44, fg_color=BLUE,
                      command=self.apply_opti).pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkButton(row, text="Remove", height=44, fg_color=RED,
                      command=self.remove_opti).pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.apply_lbl = ctk.CTkLabel(c, text="", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.apply_lbl.pack(anchor="w", padx=14, pady=(0, 14))

        # Frame gen
        self._gm_sec("FRAME GENERATION")
        c = self._gm_card()
        self.fg_var = ctk.StringVar(value=self.cfg.get("fg", "Off"))
        ctk.CTkOptionMenu(
            c, values=["Off", "Lossless Scaling", "AMD AFMF", "OptiFG", "XeFG"],
            variable=self.fg_var, command=self.on_fg,
            height=46, font=ctk.CTkFont(size=14), fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(14, 8))
        self.fg_status = ctk.CTkLabel(c, text="", text_color=DIM)
        self.fg_status.pack(anchor="w", padx=14, pady=(0, 6))
        ctk.CTkButton(c, text="Launch Lossless Scaling", height=48,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=BLUE, command=self.launch_ls).pack(fill="x", padx=14, pady=(0, 14))

        # Display quick
        self._gm_sec("DISPLAY")
        c = self._gm_card()
        rrow = ctk.CTkFrame(c, fg_color="transparent")
        rrow.pack(fill="x", padx=12, pady=(14, 8))
        self.res_btns = {}
        for res in ["1280x800", "1600x1000", "1920x1200"]:
            b = ctk.CTkButton(rrow, text=res.replace("x", "\u00d7"), height=42,
                              font=ctk.CTkFont(size=12), fg_color=PILL,
                              command=lambda r=res: self.set_res(r))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.res_btns[res] = b
        self._hl_res()
        hrow = ctk.CTkFrame(c, fg_color="transparent")
        hrow.pack(fill="x", padx=12, pady=(0, 14))
        self.hz_btns = {}
        for hz in [60, 144]:
            b = ctk.CTkButton(hrow, text=f"{hz} Hz", height=42,
                              font=ctk.CTkFont(size=13, weight="bold"), fg_color=PILL,
                              command=lambda h=hz: self.set_hz(h))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.hz_btns[hz] = b
        self._hl_hz()

    def _gm_sec(self, t):
        ctk.CTkLabel(self.gms, text=t, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=MUTED, anchor="w").pack(fill="x", pady=(16, 4), padx=4)

    def _gm_card(self):
        f = ctk.CTkFrame(self.gms, fg_color=CARD, corner_radius=14)
        f.pack(fill="x", pady=4)
        return f

    def toggle_game_menu(self):
        if self.game_menu_open:
            self.close_game_menu()
        else:
            self.open_game_menu()

    def open_game_menu(self):
        self.gmenu.grid()
        self.game_menu_open = True
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.lift()
        self.focus_force()

    def close_game_menu(self):
        self.gmenu.grid_remove()
        self.game_menu_open = False

    # ===== PAGES =====
    def _build_pages(self):
        # HOME
        home = ctk.CTkFrame(self.main, fg_color=BG)
        home.grid_columnconfigure(0, weight=1)
        home.grid_rowconfigure(1, weight=1)
        self.pages["home"] = home
        top = ctk.CTkFrame(home, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        ctk.CTkLabel(top, text="Games", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(top, text="Open Game Menu", height=40, fg_color=ACCENT,
                      text_color="#000", font=ctk.CTkFont(weight="bold"),
                      command=self.open_game_menu).pack(side="right", padx=8)
        ctk.CTkButton(top, text="Refresh", height=40, fg_color=CARD,
                      command=self.refresh_games).pack(side="right")
        self.games_frame = ctk.CTkScrollableFrame(home, fg_color="transparent")
        self.games_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        self.games_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # TOOLS
        tools = ctk.CTkFrame(self.main, fg_color=BG)
        tools.grid_columnconfigure(0, weight=1)
        self.pages["library"] = tools
        ctk.CTkLabel(tools, text="Quick Tools", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 12))
        box = ctk.CTkFrame(tools, fg_color=CARD, corner_radius=16)
        box.pack(fill="x", padx=24, pady=8)
        ctk.CTkButton(box, text="Open Game Menu (Scalers / FG / Fan / TDP)", height=56,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=ACCENT, text_color="#000",
                      command=self.open_game_menu).pack(fill="x", padx=16, pady=16)
        ctk.CTkButton(box, text="Force Close Legion Space", height=50,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=RED, command=self.force_close).pack(fill="x", padx=16, pady=(0, 16))

        # DRIVERS
        drv = ctk.CTkFrame(self.main, fg_color=BG)
        self.pages["drivers"] = drv
        ctk.CTkLabel(drv, text="Drivers", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 12))
        c = ctk.CTkFrame(drv, fg_color=CARD, corner_radius=16)
        c.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(c, text="AMD Adrenalin 25.30.44 (Legion Go)",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT).pack(anchor="w", padx=20, pady=(16, 8))
        ctk.CTkButton(c, text="Download Official Package", height=50,
                      fg_color=ORANGE, font=ctk.CTkFont(weight="bold"),
                      command=lambda: webbrowser.open(LENOVO_AMD_URL)).pack(fill="x", padx=20, pady=(0, 16))

        # SETTINGS
        st = ctk.CTkFrame(self.main, fg_color=BG)
        self.pages["settings"] = st
        ctk.CTkLabel(st, text="Settings", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 12))

        c = ctk.CTkFrame(st, fg_color=CARD, corner_radius=16)
        c.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(c, text="App Updates", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(16, 6))
        self.upd_lbl = ctk.CTkLabel(c, text=f"v{APP_VERSION} — repo must be Public for updates",
                                    text_color=DIM)
        self.upd_lbl.pack(anchor="w", padx=20, pady=(0, 8))
        self.upd_btn = ctk.CTkButton(c, text="Check & Update from GitHub", height=50,
                                     fg_color=ACCENT, text_color="#000",
                                     font=ctk.CTkFont(weight="bold"), command=self.do_update)
        self.upd_btn.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkButton(c, text="Open GitHub", height=42, fg_color=PILL,
                      command=lambda: webbrowser.open(GITHUB_PAGE)).pack(fill="x", padx=20, pady=(0, 16))

        c2 = ctk.CTkFrame(st, fg_color=CARD, corner_radius=16)
        c2.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(c2, text="Legion Button Helper", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(16, 6))
        ctk.CTkLabel(c2,
                     text="1. Force Close Legion Space (done on app start)\n"
                          "2. Run legion_button.ahk (included) as Admin once\n"
                          "3. The right Legion button opens this Game Menu\n\n"
                          "Or press F1 / Ctrl+Shift+L anytime",
                     text_color=DIM, justify="left").pack(anchor="w", padx=20, pady=(0, 12))
        ctk.CTkButton(c2, text="Open Helper Folder", height=44, fg_color=PILL,
                      command=lambda: os.startfile(APP_DIR) if sys.platform == "win32" else None).pack(
            fill="x", padx=20, pady=(0, 16))

    # ===== ACTIONS =====
    def apply_preset(self, key, tdp):
        self.setc("preset", key)
        self.setc("tdp", tdp)
        self.tdp_slider.set(tdp)
        self.tdp_lbl.configure(text=f"{tdp} W")
        for k, b in self.preset_btns.items():
            b.configure(fg_color=ACCENT if k == key else PILL,
                        text_color="#000" if k == key else TEXT)

    def on_tdp(self, v):
        val = int(float(v))
        self.tdp_lbl.configure(text=f"{val} W")
        self.setc("tdp", val)

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
        for k, b in self.res_btns.items():
            b.configure(fg_color=ACCENT if k == cur else PILL,
                        text_color="#000" if k == cur else TEXT)

    def set_hz(self, h):
        self.setc("hz", h)
        self._hl_hz()

    def _hl_hz(self):
        cur = int(self.cfg.get("hz", 144))
        for k, b in self.hz_btns.items():
            b.configure(fg_color=ACCENT if k == cur else PILL,
                        text_color="#000" if k == cur else TEXT)

    def on_fg(self, v):
        self.setc("fg", v)
        tips = {
            "Lossless Scaling": "Launch LSFG below",
            "AMD AFMF": "Enable in Adrenalin",
            "OptiFG": "Apply OptiScaler to game first",
            "XeFG": "Apply OptiScaler to game first",
            "Off": "Off \u2014 best battery/latency",
        }
        self.fg_status.configure(text=tips.get(v, ""), text_color=ACCENT if v != "Off" else DIM)

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
        msg = f"Closed: {', '.join(sorted(set(killed)))}" if killed else "Legion Space not running"
        self.fc_lbl.configure(text=msg, text_color=ACCENT if killed else DIM)

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

    def refresh_tools(self):
        if OPTISCALER_DIR.exists() and any(OPTISCALER_DIR.iterdir()):
            self.opti_status.configure(text="OptiScaler: Installed", text_color=ACCENT)
            self.opti_dl.configure(text="Update")
        else:
            self.opti_status.configure(text="OptiScaler: Not installed", text_color=DIM)
            self.opti_dl.configure(text="Download")
        if self.find_ls():
            self.fg_status.configure(text="Lossless Scaling: Found", text_color=ACCENT)

    def download_opti(self):
        if self.busy: return
        self.busy = True
        self.opti_dl.configure(text="...", state="disabled")

        def work():
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/optiscaler/OptiScaler/releases/latest",
                    headers={"User-Agent": "Legion-Custom-App"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode())
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
                self.after(0, lambda: self.opti_status.configure(text="OptiScaler: Installed", text_color=ACCENT))
            except Exception as e:
                self.after(0, lambda: self.opti_status.configure(text=f"Fail: {e}", text_color=RED))
            finally:
                self.busy = False
                self.after(0, lambda: self.opti_dl.configure(state="normal", text="Download"))
                self.after(0, self.refresh_tools)

        threading.Thread(target=work, daemon=True).start()

    def apply_opti(self):
        if not OPTISCALER_DIR.exists() or not any(OPTISCALER_DIR.iterdir()):
            self.apply_lbl.configure(text="Download OptiScaler first", text_color=RED)
            return
        folder = filedialog.askdirectory(title="Game folder")
        if not folder: return
        folder = Path(folder)
        dll = self.cfg.get("dll", "dxgi.dll")
        try:
            target, bak = folder / dll, folder / (dll + ".legionbak")
            if target.exists() and not bak.exists():
                shutil.copy2(target, bak)
            for item in OPTISCALER_DIR.iterdir():
                dest = folder / item.name
                if item.is_file(): shutil.copy2(item, dest)
                elif item.is_dir():
                    if dest.exists(): shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            for cand in ["OptiScaler.dll", "dxgi.dll", "winmm.dll"]:
                p = OPTISCALER_DIR / cand
                if p.exists() and p.name.lower() != dll.lower():
                    src = folder / p.name
                    if src.exists(): shutil.copy2(src, folder / dll)
                    break
            self.applied[str(folder.resolve())] = {"dll": dll}
            self._save(APPLIED_LOG, self.applied)
            self.apply_lbl.configure(text=f"Applied → {folder.name}", text_color=ACCENT)
            self.refresh_games()
        except Exception as e:
            self.apply_lbl.configure(text=str(e), text_color=RED)

    def remove_opti(self):
        folder = filedialog.askdirectory(title="Remove OptiScaler from...")
        if not folder: return
        folder = Path(folder)
        try:
            for dll in ["dxgi.dll", "winmm.dll", "version.dll"]:
                bak = folder / (dll + ".legionbak")
                if bak.exists():
                    shutil.copy2(bak, folder / dll); bak.unlink()
            for name in ["OptiScaler.dll", "OptiScaler.ini", "nvngx.dll", "libxess.dll"]:
                p = folder / name
                if p.exists(): p.unlink()
            key = str(folder.resolve())
            if key in self.applied:
                del self.applied[key]
                self._save(APPLIED_LOG, self.applied)
            self.apply_lbl.configure(text=f"Removed from {folder.name}", text_color=ACCENT)
            self.refresh_games()
        except Exception as e:
            self.apply_lbl.configure(text=str(e), text_color=RED)

    def find_ls(self):
        cands = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
        ]
        for d in "CDEF":
            cands.append(Path(f"{d}:/SteamLibrary/steamapps/common/Lossless Scaling/LosslessScaling.exe"))
        for p in cands:
            if p.exists(): return p
        return None

    def launch_ls(self):
        p = self.find_ls()
        if p:
            subprocess.Popen([str(p)])
        else:
            subprocess.Popen(["cmd", "/c", "start", "steam://rungameid/993090"], shell=True)

    def do_update(self):
        if self.busy: return
        self.busy = True
        self.upd_btn.configure(state="disabled", text="Updating...")
        self.upd_lbl.configure(text="Downloading... (repo must be Public)", text_color=ORANGE)

        def work():
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    zp = Path(tmp) / "r.zip"
                    req = urllib.request.Request(GITHUB_ZIP, headers={"User-Agent": "Legion-Custom-App"})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        zp.write_bytes(r.read())
                    out = Path(tmp) / "e"; out.mkdir()
                    with zipfile.ZipFile(zp) as z: z.extractall(out)
                    inner = next(out.iterdir())
                    updated = []
                    for fname in ["main.py", "requirements.txt", "README.md", "install.bat", "run.bat", "legion_button.ahk"]:
                        src = inner / fname
                        if src.exists():
                            tmpd = APP_DIR / (fname + ".new")
                            shutil.copy2(src, tmpd)
                            tmpd.replace(APP_DIR / fname)
                            updated.append(fname)
                    if updated:
                        self.after(0, lambda: self.upd_lbl.configure(text="Updated — restarting", text_color=ACCENT))
                        time.sleep(1.2)
                        subprocess.Popen([sys.executable, str(APP_DIR / "main.py")] + sys.argv[1:], cwd=str(APP_DIR))
                        self.after(0, self.destroy)
                    else:
                        self.after(0, lambda: self.upd_lbl.configure(text="Up to date", text_color=ACCENT))
            except Exception as e:
                msg = str(e)
                if "404" in msg:
                    msg = "404 — make GitHub repo PUBLIC"
                self.after(0, lambda: self.upd_lbl.configure(text=msg, text_color=RED))
            finally:
                self.busy = False
                self.after(0, lambda: self.upd_btn.configure(state="normal", text="Check & Update from GitHub"))

        threading.Thread(target=work, daemon=True).start()

    def refresh_games(self):
        for w in self.games_frame.winfo_children():
            w.destroy()
        games = self.scan_games()
        if not games:
            ctk.CTkLabel(self.games_frame, text="No games found", text_color=MUTED).grid(
                row=0, column=0, pady=60)
            return
        for i, g in enumerate(games):
            r, c = divmod(i, 4)
            card = ctk.CTkFrame(self.games_frame, width=230, height=140, corner_radius=14, fg_color=CARD)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            card.grid_propagate(False)
            ok = str(Path(g["path"]).parent.resolve()) in self.applied
            ctk.CTkLabel(card, text=g["name"][:22] + (" \u2713" if ok else ""),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=ACCENT if ok else TEXT).pack(pady=(18, 8), padx=8)
            if Path(g["path"]).exists():
                ctk.CTkButton(card, text="Play", width=100, height=34,
                              fg_color=ACCENT, text_color="#000",
                              command=lambda p=g["path"]: subprocess.Popen(
                                  [p], cwd=str(Path(p).parent))).pack()

    def scan_games(self):
        found = []
        bases = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/steamapps/common",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam/steamapps/common",
        ]
        for d in "CDEF":
            bases.append(Path(f"{d}:/SteamLibrary/steamapps/common"))
        for base in bases:
            if not base.exists(): continue
            for gdir in base.iterdir():
                if not gdir.is_dir(): continue
                exes = list(gdir.glob("*.exe"))
                if not exes: continue
                main = next((e for e in exes if gdir.name.lower() in e.stem.lower()), exes[0])
                found.append({"name": gdir.name, "path": str(main)})
        return list({g["name"]: g for g in found}.values())[:48]


if __name__ == "__main__":
    App().mainloop()

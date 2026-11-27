#!/usr/bin/env python3
"""
Legion Custom App v1.2.0
Legion Space-style quick menu for first-gen Legion Go (Z1 Extreme)
"""

import customtkinter as ctk
import subprocess
import os
import sys
import webbrowser
from pathlib import Path
import json
import threading
import urllib.request
import zipfile
import shutil
import tempfile
import time
import math

try:
    import psutil
except ImportError:
    psutil = None

APP_NAME = "Legion Custom"
APP_VERSION = "1.2.0"
GITHUB_REPO = "devin12310-prog/Legion-Custom-App"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
GITHUB_PAGE = f"https://github.com/{GITHUB_REPO}"

APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "config.json"
OPTISCALER_DIR = APP_DIR / "OptiScaler"

LENOVO_AMD_DRIVER_URL = "https://support.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1/downloads/ds565497-amd-graphics-driver-for-windows-11-64-bit-legion-go-8apu1"
LENOVO_SUPPORT_URL = "https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1"

LEGION_SPACE_PROCESSES = [
    "LegionSpace.exe", "LSDaemon.exe", "LegionSettingMenu.exe",
    "LegionGameWidget.exe", "LegionGameWidget_Sub.exe",
    "LegionSpaceComponent.exe", "LegionSpaceToast.exe",
]

DEFAULT_CONFIG = {
    "tdp": 25,
    "preset": "Balanced",
    "fan_mode": "Smart",
    "scaler": "None",
    "frame_gen": "Off",
    "resolution": "1600x1000",
    "refresh": 144,
    "fps_limit": 0,
}

# Colors matching Legion Space vibe
BG = "#0d1117"
PANEL = "#161b22"
CARD = "#1c2333"
ACCENT = "#00d2a0"          # teal/green like Legion Space
ACCENT_DIM = "#00a87e"
BLUE = "#3d7eff"
RED = "#ff4757"
ORANGE = "#ffa502"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
TEXT_MUTED = "#484f58"
PILL_BG = "#21262d"
PILL_ACTIVE = "#00d2a0"

ctk.set_appearance_mode("dark")


class LegionCustomApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))

        self.config = self.load_config()
        self.right_visible = False
        self.games = []
        self.download_in_progress = False
        self.update_in_progress = False
        self.stats_job = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_main()
        self._build_right()

        self.bind("<Control-Shift-L>", lambda e: self.toggle_right())
        self.bind("<F1>", lambda e: self.toggle_right())
        self.bind("<Escape>", lambda e: self.hide_right())

        if "--menu" in sys.argv:
            self.after(200, self.show_right)

        self.after(300, self.refresh_games)
        self.after(400, self.refresh_tool_status)
        self.after(600, self.start_stats_loop)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def set_cfg(self, k, v):
        self.config[k] = v
        self.save_config()

    # ===================== MAIN UI =====================
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.main, height=64, fg_color=PANEL, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        ctk.CTkLabel(top, text="LEGION CUSTOM", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=22, pady=16)
        ctk.CTkLabel(top, text=f"v{APP_VERSION}", font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack(side="left", pady=16)

        self.menu_btn = ctk.CTkButton(
            top, text="Quick Menu  ▶", width=150, height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
            command=self.toggle_right
        )
        self.menu_btn.pack(side="right", padx=18)

        body = ctk.CTkFrame(self.main, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=14)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(body, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(hdr, text="Games", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="Refresh", width=90, height=30, fg_color=CARD,
                      hover_color=PILL_BG, command=self.refresh_games).pack(side="right")

        self.games_scroll = ctk.CTkScrollableFrame(body, fg_color=PANEL, corner_radius=14)
        self.games_scroll.grid(row=1, column=0, sticky="nsew")
        self.games_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

    # ===================== RIGHT PANEL (Legion Space style) =====================
    def _build_right(self):
        self.right = ctk.CTkFrame(self, width=400, fg_color=PANEL, corner_radius=0)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.grid_propagate(False)
        self.right.grid_remove()

        # Header
        hdr = ctk.CTkFrame(self.right, fg_color="transparent", height=52)
        hdr.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(hdr, text="QUICK MENU", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="✕", width=32, height=32, fg_color="transparent",
                      hover_color=CARD, text_color=TEXT_DIM,
                      command=self.hide_right).pack(side="right")

        self.rscroll = ctk.CTkScrollableFrame(self.right, fg_color="transparent")
        self.rscroll.pack(fill="both", expand=True, padx=10, pady=6)

        # ---- FORCE CLOSE ----
        self._sec("LEGION SPACE")
        fc = self._card()
        ctk.CTkButton(
            fc, text="FORCE CLOSE LEGION SPACE", height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=RED, hover_color="#e03e4e",
            command=self.force_close
        ).pack(fill="x", padx=12, pady=(12, 4))
        self.fc_status = ctk.CTkLabel(fc, text="Ready", text_color=TEXT_MUTED,
                                      font=ctk.CTkFont(size=11))
        self.fc_status.pack(anchor="w", padx=12, pady=(0, 10))

        # ---- PERFORMANCE MODES (like Legion Space) ----
        self._sec("PERFORMANCE")
        perf = self._card()

        mode_row = ctk.CTkFrame(perf, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=(12, 8))

        self.mode_btns = {}
        for i, (key, label) in enumerate([
            ("Performance", "High Performance"),
            ("Quiet", "Power Saving"),
            ("Custom", "Custom"),
        ]):
            b = ctk.CTkButton(
                mode_row, text=label, height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=PILL_BG, hover_color=CARD,
                command=lambda k=key: self.set_mode(k)
            )
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.mode_btns[key] = b

        self._update_mode_buttons()

        # Live stats row
        stats_row = ctk.CTkFrame(perf, fg_color="transparent")
        stats_row.pack(fill="x", padx=10, pady=(4, 12))

        self.stat_labels = {}
        for key, name in [("cpu", "CPU"), ("gpu", "GPU"), ("vram", "VRAM"), ("ram", "RAM")]:
            box = ctk.CTkFrame(stats_row, fg_color=PILL_BG, corner_radius=10)
            box.pack(side="left", expand=True, fill="x", padx=3)
            self.stat_labels[key] = ctk.CTkLabel(
                box, text="--%", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT
            )
            self.stat_labels[key].pack(pady=(8, 0))
            ctk.CTkLabel(box, text=name, font=ctk.CTkFont(size=11),
                         text_color=TEXT_DIM).pack(pady=(0, 8))

        # ---- TDP / THERMAL ----
        self._sec("TDP / THERMAL")
        tdpf = self._card()

        tdp_modes = ctk.CTkFrame(tdpf, fg_color="transparent")
        tdp_modes.pack(fill="x", padx=10, pady=(12, 6))

        self.tdp_mode_btns = {}
        for key, label in [("Quiet", "Quiet"), ("Balanced", "Balanced"),
                           ("Performance", "Performance"), ("Custom", "Custom")]:
            b = ctk.CTkButton(
                tdp_modes, text=label, height=34,
                font=ctk.CTkFont(size=12),
                fg_color=PILL_BG, hover_color=CARD,
                command=lambda k=key: self.set_tdp_mode(k)
            )
            b.pack(side="left", expand=True, fill="x", padx=2)
            self.tdp_mode_btns[key] = b

        self._update_tdp_buttons()

        self.tdp_slider = ctk.CTkSlider(
            tdpf, from_=8, to=40, number_of_steps=32,
            progress_color=ACCENT, button_color=ACCENT,
            command=self.on_tdp_slide
        )
        self.tdp_slider.set(self.config.get("tdp", 25))
        self.tdp_slider.pack(fill="x", padx=14, pady=(8, 2))

        self.tdp_val = ctk.CTkLabel(
            tdpf, text=f"{int(self.config.get('tdp', 25))} W",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT
        )
        self.tdp_val.pack(pady=(0, 6))

        ctk.CTkButton(
            tdpf, text="Apply TDP", height=36,
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
            font=ctk.CTkFont(weight="bold"),
            command=self.apply_tdp
        ).pack(fill="x", padx=12, pady=(0, 12))

        # ---- FAN ----
        self._sec("FAN")
        fanf = self._card()

        fan_row = ctk.CTkFrame(fanf, fg_color="transparent")
        fan_row.pack(fill="x", padx=10, pady=(12, 8))

        self.fan_btns = {}
        for key, label in [("Smart", "Smart"), ("Full", "Full Speed")]:
            b = ctk.CTkButton(
                fan_row, text=label, height=36,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=PILL_BG, hover_color=CARD,
                command=lambda k=key: self.set_fan(k)
            )
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.fan_btns[key] = b
        self._update_fan_buttons()

        # Simple fan curve visual
        self.fan_canvas = ctk.CTkCanvas(
            fanf, height=90, bg=PILL_BG, highlightthickness=0
        )
        self.fan_canvas.pack(fill="x", padx=12, pady=(0, 12))
        self.after(100, self.draw_fan_curve)

        # ---- DISPLAY ----
        self._sec("DISPLAY")
        disp = self._card()

        ctk.CTkLabel(disp, text="Resolution", text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=(10, 4))

        res_row = ctk.CTkFrame(disp, fg_color="transparent")
        res_row.pack(fill="x", padx=8, pady=(0, 8))

        self.res_btns = {}
        for res in ["1280x800", "1600x1000", "1920x1200"]:
            b = ctk.CTkButton(
                res_row, text=res, height=32, width=110,
                font=ctk.CTkFont(size=11),
                fg_color=PILL_BG, hover_color=CARD,
                command=lambda r=res: self.set_res(r)
            )
            b.pack(side="left", padx=3)
            self.res_btns[res] = b
        self._update_res_buttons()

        ctk.CTkLabel(disp, text="Refresh Rate", text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=(4, 4))

        ref_row = ctk.CTkFrame(disp, fg_color="transparent")
        ref_row.pack(fill="x", padx=8, pady=(0, 12))

        self.ref_btns = {}
        for hz in [60, 144]:
            b = ctk.CTkButton(
                ref_row, text=f"{hz}Hz", height=32, width=90,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=PILL_BG, hover_color=CARD,
                command=lambda h=hz: self.set_refresh(h)
            )
            b.pack(side="left", padx=3)
            self.ref_btns[hz] = b
        self._update_ref_buttons()

        # ---- SCALERS ----
        self._sec("SCALERS & FRAME GEN")
        sc = self._card()

        self.tool_status = ctk.CTkLabel(
            sc, text="Scanning...", text_color=TEXT_DIM,
            font=ctk.CTkFont(size=12), justify="left"
        )
        self.tool_status.pack(anchor="w", padx=12, pady=(10, 6))

        row = ctk.CTkFrame(sc, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 6))

        self.opti_btn = ctk.CTkButton(
            row, text="Download OptiScaler", height=34,
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
            command=self.download_optiscaler
        )
        self.opti_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            row, text="Folder", width=70, height=34,
            fg_color=PILL_BG, hover_color=CARD,
            command=self.open_optiscaler_folder
        ).pack(side="left")

        self.lossless_btn = ctk.CTkButton(
            sc, text="Launch Lossless Scaling", height=34,
            fg_color=BLUE, hover_color="#2a5fd4",
            command=self.launch_lossless
        )
        self.lossless_btn.pack(fill="x", padx=10, pady=(0, 12))

        # ---- DRIVERS ----
        self._sec("DRIVERS")
        dr = self._card()
        ctk.CTkButton(
            dr, text="AMD Adrenalin 25.30.44 (Legion Go)", height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color=ORANGE, hover_color="#e69500",
            command=lambda: webbrowser.open(LENOVO_AMD_DRIVER_URL)
        ).pack(fill="x", padx=12, pady=(12, 12))

        # ---- UPDATES ----
        self._sec("APP UPDATES")
        up = self._card()
        self.upd_status = ctk.CTkLabel(
            up, text=f"Current: v{APP_VERSION}", text_color=TEXT_DIM,
            font=ctk.CTkFont(size=12)
        )
        self.upd_status.pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkButton(
            up, text="Check & Update from GitHub", height=38,
            font=ctk.CTkFont(weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
            command=self.check_and_update
        ).pack(fill="x", padx=12, pady=(0, 12))

    def _sec(self, t):
        ctk.CTkLabel(
            self.rscroll, text=t, font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(14, 3), padx=2)

    def _card(self):
        f = ctk.CTkFrame(self.rscroll, fg_color=CARD, corner_radius=12)
        f.pack(fill="x", pady=(0, 2))
        return f

    # ===================== BUTTON STATE HELPERS =====================
    def _update_mode_buttons(self):
        cur = self.config.get("preset", "Balanced")
        # Map Balanced -> treat as custom-ish for the top 3
        for k, b in self.mode_btns.items():
            if (k == "Performance" and cur == "Performance") or \
               (k == "Quiet" and cur == "Quiet") or \
               (k == "Custom" and cur in ("Custom", "Balanced")):
                b.configure(fg_color=ACCENT, text_color="#000")
            else:
                b.configure(fg_color=PILL_BG, text_color=TEXT)

    def _update_tdp_buttons(self):
        cur = self.config.get("preset", "Balanced")
        for k, b in self.tdp_mode_btns.items():
            if k == cur:
                b.configure(fg_color=ACCENT, text_color="#000")
            else:
                b.configure(fg_color=PILL_BG, text_color=TEXT)

    def _update_fan_buttons(self):
        cur = self.config.get("fan_mode", "Smart")
        for k, b in self.fan_btns.items():
            if k == cur:
                b.configure(fg_color=ACCENT, text_color="#000")
            else:
                b.configure(fg_color=PILL_BG, text_color=TEXT)

    def _update_res_buttons(self):
        cur = self.config.get("resolution", "1600x1000")
        for r, b in self.res_btns.items():
            if r == cur:
                b.configure(fg_color=ACCENT, text_color="#000")
            else:
                b.configure(fg_color=PILL_BG, text_color=TEXT)

    def _update_ref_buttons(self):
        cur = int(self.config.get("refresh", 144))
        for hz, b in self.ref_btns.items():
            if hz == cur:
                b.configure(fg_color=ACCENT, text_color="#000")
            else:
                b.configure(fg_color=PILL_BG, text_color=TEXT)

    # ===================== ACTIONS =====================
    def set_mode(self, key):
        mapping = {"Performance": 35, "Quiet": 15, "Custom": self.config.get("tdp", 25)}
        self.set_cfg("preset", key if key != "Custom" else "Custom")
        tdp = mapping.get(key, 25)
        self.tdp_slider.set(tdp)
        self.tdp_val.configure(text=f"{tdp} W")
        self.set_cfg("tdp", tdp)
        self._update_mode_buttons()
        self._update_tdp_buttons()

    def set_tdp_mode(self, key):
        mapping = {"Quiet": 15, "Balanced": 25, "Performance": 35}
        self.set_cfg("preset", key)
        if key in mapping:
            tdp = mapping[key]
            self.tdp_slider.set(tdp)
            self.tdp_val.configure(text=f"{tdp} W")
            self.set_cfg("tdp", tdp)
        self._update_tdp_buttons()
        self._update_mode_buttons()

    def on_tdp_slide(self, v):
        val = int(float(v))
        self.tdp_val.configure(text=f"{val} W")
        self.set_cfg("tdp", val)
        self.set_cfg("preset", "Custom")
        self._update_tdp_buttons()
        self._update_mode_buttons()

    def set_fan(self, key):
        self.set_cfg("fan_mode", key)
        self._update_fan_buttons()
        self.draw_fan_curve()

    def set_res(self, res):
        self.set_cfg("resolution", res)
        self._update_res_buttons()

    def set_refresh(self, hz):
        self.set_cfg("refresh", hz)
        self._update_ref_buttons()

    def draw_fan_curve(self):
        c = self.fan_canvas
        c.delete("all")
        w = c.winfo_width() or 340
        h = 90
        # grid
        for i in range(1, 5):
            y = h - (i * h / 5)
            c.create_line(10, y, w-10, y, fill="#2a303c", width=1)

        mode = self.config.get("fan_mode", "Smart")
        if mode == "Full":
            points = [(0.0, 0.9), (0.2, 0.95), (0.5, 1.0), (1.0, 1.0)]
        else:
            points = [(0.0, 0.15), (0.3, 0.25), (0.5, 0.45), (0.7, 0.7), (1.0, 0.95)]

        coords = []
        for x_pct, y_pct in points:
            x = 10 + x_pct * (w - 20)
            y = h - 8 - y_pct * (h - 20)
            coords.extend([x, y])

        if len(coords) >= 4:
            c.create_line(*coords, fill=ACCENT, width=2.5, smooth=True)
            for i in range(0, len(coords), 2):
                c.create_oval(coords[i]-3, coords[i+1]-3,
                              coords[i]+3, coords[i+1]+3,
                              fill=ACCENT, outline="")

    # ===================== PANEL TOGGLE =====================
    def toggle_right(self):
        if self.right_visible:
            self.hide_right()
        else:
            self.show_right()

    def show_right(self):
        self.right.grid()
        self.right_visible = True
        self.menu_btn.configure(text="Close  ◀")
        self.draw_fan_curve()

    def hide_right(self):
        self.right.grid_remove()
        self.right_visible = False
        self.menu_btn.configure(text="Quick Menu  ▶")

    # ===================== FORCE CLOSE =====================
    def force_close(self):
        killed = []
        if psutil:
            for p in psutil.process_iter(["name"]):
                try:
                    n = p.info["name"]
                    if n and n.lower() in [x.lower() for x in LEGION_SPACE_PROCESSES]:
                        p.kill()
                        killed.append(n)
                except Exception:
                    pass
        else:
            for name in LEGION_SPACE_PROCESSES:
                try:
                    r = subprocess.run(
                        ["taskkill", "/F", "/IM", name], capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    if r.returncode == 0:
                        killed.append(name)
                except Exception:
                    pass
        if killed:
            self.fc_status.configure(text=f"Closed: {', '.join(sorted(set(killed)))}", text_color=ACCENT)
        else:
            self.fc_status.configure(text="No Legion Space processes running", text_color=TEXT_MUTED)

    # ===================== STATS =====================
    def start_stats_loop(self):
        self.update_stats()
        self.stats_job = self.after(2000, self.start_stats_loop)

    def update_stats(self):
        if not psutil:
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.stat_labels["cpu"].configure(text=f"{cpu:.0f}%")
            self.stat_labels["ram"].configure(text=f"{ram:.0f}%")
            # GPU / VRAM placeholders (need ADLX or similar for real values)
            self.stat_labels["gpu"].configure(text="--%")
            self.stat_labels["vram"].configure(text="--%")
        except Exception:
            pass

    # ===================== TOOLS =====================
    def find_lossless(self):
        paths = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
        ]
        for d in "CDEF":
            paths.append(Path(f"{d}:/SteamLibrary/steamapps/common/Lossless Scaling/LosslessScaling.exe"))
        for p in paths:
            if p.exists():
                return p
        return None

    def refresh_tool_status(self):
        lines = []
        if OPTISCALER_DIR.exists() and any(OPTISCALER_DIR.iterdir()):
            lines.append("OptiScaler: Installed")
            self.opti_btn.configure(text="Update OptiScaler")
        else:
            lines.append("OptiScaler: Not installed")
            self.opti_btn.configure(text="Download OptiScaler")

        ls = self.find_lossless()
        if ls:
            lines.append("Lossless Scaling: Found")
            self.lossless_btn.configure(text="Launch Lossless Scaling", state="normal")
        else:
            lines.append("Lossless Scaling: Not found")
            self.lossless_btn.configure(text="Lossless Scaling (not found)")

        self.tool_status.configure(text="\n".join(lines))

    def download_optiscaler(self):
        if self.download_in_progress:
            return
        self.download_in_progress = True
        self.opti_btn.configure(text="Downloading...", state="disabled")

        def work():
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/optiscaler/OptiScaler/releases/latest",
                    headers={"User-Agent": "Legion-Custom-App"}
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode())
                tag = data.get("tag_name", "?")
                url = next((a["browser_download_url"] for a in data.get("assets", [])
                            if a["name"].lower().endswith(".zip")), data.get("zipball_url"))
                with tempfile.TemporaryDirectory() as tmp:
                    zp = Path(tmp) / "o.zip"
                    urllib.request.urlretrieve(url, zp)
                    out = Path(tmp) / "e"
                    out.mkdir()
                    with zipfile.ZipFile(zp) as z:
                        z.extractall(out)
                    if OPTISCALER_DIR.exists():
                        shutil.rmtree(OPTISCALER_DIR)
                    OPTISCALER_DIR.mkdir()
                    items = list(out.iterdir())
                    src = items[0] if len(items) == 1 and items[0].is_dir() else out
                    for it in src.iterdir():
                        d = OPTISCALER_DIR / it.name
                        if it.is_dir():
                            shutil.copytree(it, d)
                        else:
                            shutil.copy2(it, d)
                self.after(0, self.refresh_tool_status)
            except Exception as e:
                print(e)
            finally:
                self.download_in_progress = False
                self.after(0, lambda: self.opti_btn.configure(state="normal"))
                self.after(0, self.refresh_tool_status)

        threading.Thread(target=work, daemon=True).start()

    def open_optiscaler_folder(self):
        OPTISCALER_DIR.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OPTISCALER_DIR)

    def launch_lossless(self):
        p = self.find_lossless()
        if p:
            subprocess.Popen([str(p)])
        else:
            try:
                subprocess.Popen(["cmd", "/c", "start", "steam://rungameid/993090"], shell=True)
            except Exception:
                pass

    def apply_tdp(self):
        tdp = int(self.config.get("tdp", 25))
        for cand in [APP_DIR / "ryzenadj.exe", Path("C:/tools/ryzenadj/ryzenadj.exe")]:
            if cand.exists():
                try:
                    subprocess.Popen(
                        [str(cand), f"--stapm-limit={tdp*1000}",
                         f"--fast-limit={tdp*1000}", f"--slow-limit={tdp*1000}"],
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                except Exception:
                    pass
                return
        print(f"[TDP] {tdp}W - place ryzenadj.exe next to app for real control")

    # ===================== UPDATER =====================
    def check_and_update(self):
        if self.update_in_progress:
            return
        self.update_in_progress = True
        self.upd_status.configure(text="Updating from GitHub...")

        def work():
            try:
                updated = []
                for fname in ["main.py", "requirements.txt", "README.md", "install.bat", "run.bat"]:
                    try:
                        req = urllib.request.Request(
                            f"{GITHUB_RAW}/{fname}",
                            headers={"User-Agent": "Legion-Custom-App"}
                        )
                        with urllib.request.urlopen(req, timeout=20) as r:
                            content = r.read()
                        target = APP_DIR / fname
                        if not target.exists() or target.read_bytes() != content:
                            target.write_bytes(content)
                            updated.append(fname)
                    except Exception as e:
                        print(fname, e)
                if updated:
                    self.after(0, lambda: self.upd_status.configure(
                        text=f"Updated {len(updated)} files. Restarting...", text_color=ACCENT))
                    time.sleep(1.2)
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    self.after(0, lambda: self.upd_status.configure(
                        text="Already up to date", text_color=ACCENT))
            except Exception as e:
                self.after(0, lambda: self.upd_status.configure(text=f"Failed: {e}", text_color=RED))
            finally:
                self.update_in_progress = False

        threading.Thread(target=work, daemon=True).start()

    # ===================== GAMES =====================
    def refresh_games(self):
        for w in self.games_scroll.winfo_children():
            w.destroy()
        self.games = self.scan_games()
        if not self.games:
            ctk.CTkLabel(self.games_scroll, text="No games found yet",
                         text_color=TEXT_MUTED).grid(row=0, column=0, columnspan=4, pady=50)
            return
        for i, g in enumerate(self.games):
            r, c = divmod(i, 4)
            card = ctk.CTkFrame(self.games_scroll, width=210, height=120,
                                corner_radius=12, fg_color=CARD)
            card.grid(row=r, column=c, padx=7, pady=7, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=g["name"][:26], font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT, wraplength=190).pack(pady=(18, 8), padx=8)
            if Path(g["path"]).exists():
                ctk.CTkButton(card, text="Play", width=90, height=28,
                              fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
                              command=lambda p=g["path"]: self.launch_game(p)).pack()

    def launch_game(self, path):
        try:
            subprocess.Popen([path], cwd=str(Path(path).parent))
        except Exception as e:
            print(e)

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
                if gdir.is_dir():
                    exes = list(gdir.glob("*.exe"))
                    if not exes:
                        continue
                    main = next((e for e in exes if gdir.name.lower() in e.stem.lower()), exes[0])
                    found.append({"name": gdir.name, "path": str(main)})
        return list({g["name"]: g for g in found}.values())[:40]


if __name__ == "__main__":
    app = LegionCustomApp()
    app.mainloop()

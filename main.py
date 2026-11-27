#!/usr/bin/env python3
"""
Legion Custom App v1.1.0
Custom quick-settings + game launcher for first-gen Legion Go (Z1 Extreme)
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

try:
    import psutil
except ImportError:
    psutil = None

# ===================== APP INFO =====================
APP_NAME = "Legion Custom"
APP_VERSION = "1.1.0"
GITHUB_REPO = "devin12310-prog/Legion-Custom-App"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
GITHUB_PAGE = f"https://github.com/{GITHUB_REPO}"

APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "config.json"
OPTISCALER_DIR = APP_DIR / "OptiScaler"

# Official links
LENOVO_AMD_DRIVER_URL = "https://support.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1/downloads/ds565497-amd-graphics-driver-for-windows-11-64-bit-legion-go-8apu1"
LENOVO_SUPPORT_URL = "https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1"
AMD_SUPPORT_URL = "https://www.amd.com/en/support"

LEGION_RESOLUTIONS = ["1600x1000", "1280x800", "1920x1200", "1200x750", "800x500", "640x400"]

LEGION_SPACE_PROCESSES = [
    "LegionSpace.exe", "LSDaemon.exe", "LegionSettingMenu.exe",
    "LegionGameWidget.exe", "LegionGameWidget_Sub.exe",
    "LegionSpaceComponent.exe", "LegionSpaceToast.exe",
]

DEFAULT_CONFIG = {
    "tdp": 25,
    "preset": "Balanced",
    "scaler": "None",
    "frame_gen": "Off",
    "resolution": "1600x1000",
    "refresh": 144,
    "brightness": 70,
    "mapper_profile": "Default",
}

# Colors - Decky / EmuDeck inspired
BG_DARK = "#0b0d12"
BG_PANEL = "#12151c"
BG_CARD = "#1a1e28"
BG_CARD_HOVER = "#222833"
ACCENT = "#3d7eff"
ACCENT_HOVER = "#2a5fd4"
GREEN = "#1db954"
GREEN_HOVER = "#17a34a"
RED = "#e74c3c"
RED_HOVER = "#c0392b"
ORANGE = "#e67e22"
TEXT = "#e8eaed"
TEXT_DIM = "#8b93a7"
TEXT_MUTED = "#5c6578"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class LegionCustomApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=BG_DARK)

        # Bring to front briefly
        self.attributes("-topmost", True)
        self.after(600, lambda: self.attributes("-topmost", False))

        self.config = self.load_config()
        self.right_panel_visible = False
        self.games = []
        self.download_in_progress = False
        self.update_in_progress = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

        # Hotkeys
        self.bind("<Control-Shift-L>", lambda e: self.toggle_right_panel())
        self.bind("<F1>", lambda e: self.toggle_right_panel())
        self.bind("<Escape>", lambda e: self.hide_right_panel())

        if "--menu" in sys.argv:
            self.after(250, self.show_right_panel)

        self.after(300, self.refresh_games)
        self.after(500, self.refresh_tool_status)

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
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

    def update_config(self, key, value):
        self.config[key] = value
        self.save_config()

    # ------------------------------------------------------------------
    # UI BUILD
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Main area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_DARK)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Top bar
        top = ctk.CTkFrame(self.main_frame, height=70, corner_radius=0, fg_color=BG_PANEL)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        ctk.CTkLabel(
            top, text="LEGION CUSTOM",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT
        ).pack(side="left", padx=24, pady=18)

        ctk.CTkLabel(
            top, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=13), text_color=TEXT_MUTED
        ).pack(side="left", pady=18)

        self.menu_btn = ctk.CTkButton(
            top, text="Quick Menu  ▶",
            width=160, height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self.toggle_right_panel
        )
        self.menu_btn.pack(side="right", padx=20)

        # Games area
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            header, text="Games",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=100, height=32,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            command=self.refresh_games
        ).pack(side="right")

        self.games_scroll = ctk.CTkScrollableFrame(
            content, fg_color=BG_PANEL, corner_radius=16
        )
        self.games_scroll.grid(row=1, column=0, sticky="nsew")
        self.games_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Right panel (Quick Menu)
        self.right_panel = ctk.CTkFrame(self, width=420, corner_radius=0, fg_color=BG_PANEL)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_remove()

        self._build_right_panel()

    def _build_right_panel(self):
        # Header
        hdr = ctk.CTkFrame(self.right_panel, fg_color="transparent", height=60)
        hdr.pack(fill="x", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            hdr, text="QUICK MENU",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="✕", width=36, height=36,
            fg_color="transparent", hover_color=BG_CARD,
            text_color=TEXT_DIM, command=self.hide_right_panel
        ).pack(side="right")

        self.panel_scroll = ctk.CTkScrollableFrame(
            self.right_panel, fg_color="transparent"
        )
        self.panel_scroll.pack(fill="both", expand=True, padx=12, pady=4)

        # ===== FORCE CLOSE (very prominent) =====
        self._section("LEGION SPACE")
        force_card = self._card()

        ctk.CTkLabel(
            force_card,
            text="Stop Legion Space so buttons don't conflict",
            text_color=TEXT_DIM, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkButton(
            force_card, text="FORCE CLOSE LEGION SPACE",
            height=44, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=RED, hover_color=RED_HOVER,
            command=self.force_close_legion_space
        ).pack(fill="x", padx=14, pady=(0, 6))

        self.ls_status = ctk.CTkLabel(force_card, text="Ready", text_color=TEXT_MUTED)
        self.ls_status.pack(anchor="w", padx=14, pady=(0, 12))

        # ===== PERFORMANCE =====
        self._section("PERFORMANCE")
        perf = self._card()

        self.preset_var = ctk.StringVar(value=self.config.get("preset", "Balanced"))
        for name in ["Quiet", "Balanced", "Performance", "Custom"]:
            ctk.CTkRadioButton(
                perf, text=name, variable=self.preset_var, value=name,
                command=self.on_preset_change, font=ctk.CTkFont(size=14)
            ).pack(anchor="w", padx=14, pady=5)

        # ===== TDP =====
        self._section("TDP LIMIT")
        tdp = self._card()

        self.tdp_slider = ctk.CTkSlider(
            tdp, from_=8, to=40, number_of_steps=32,
            command=self.on_tdp_change, progress_color=ACCENT
        )
        self.tdp_slider.set(self.config.get("tdp", 25))
        self.tdp_slider.pack(fill="x", padx=14, pady=(14, 4))

        self.tdp_label = ctk.CTkLabel(
            tdp, text=f"{int(self.config.get('tdp', 25))} W",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT
        )
        self.tdp_label.pack(pady=(0, 6))

        ctk.CTkButton(
            tdp, text="Apply TDP", height=38,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self.apply_tdp
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ===== DISPLAY =====
        self._section("DISPLAY")
        disp = self._card()

        ctk.CTkLabel(disp, text="Resolution", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(12, 2))
        self.res_var = ctk.StringVar(value=self.config.get("resolution", "1600x1000"))
        ctk.CTkOptionMenu(
            disp, values=LEGION_RESOLUTIONS, variable=self.res_var,
            command=lambda v: self.update_config("resolution", v),
            fg_color=BG_CARD, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(disp, text="Refresh Rate", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(4, 2))
        self.refresh_var = ctk.StringVar(value=str(self.config.get("refresh", 144)))
        ctk.CTkOptionMenu(
            disp, values=["60", "120", "144"], variable=self.refresh_var,
            command=lambda v: self.update_config("refresh", int(v)),
            fg_color=BG_CARD, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ===== SCALERS & FRAME GEN =====
        self._section("SCALERS & FRAME GEN")
        scale = self._card()

        ctk.CTkLabel(scale, text="Upscaler", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(12, 2))
        self.scaler_var = ctk.StringVar(value=self.config.get("scaler", "None"))
        ctk.CTkOptionMenu(
            scale,
            values=["None", "FSR 2 / 3 / 4", "XeSS", "OptiScaler (Auto)", "DLSS Spoof"],
            variable=self.scaler_var,
            command=lambda v: self.update_config("scaler", v),
            fg_color=BG_CARD, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(scale, text="Frame Generation", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(4, 2))
        self.fg_var = ctk.StringVar(value=self.config.get("frame_gen", "Off"))
        ctk.CTkOptionMenu(
            scale,
            values=["Off", "Lossless Scaling (LSFG)", "AMD AFMF", "OptiFG", "XeFG"],
            variable=self.fg_var,
            command=lambda v: self.update_config("frame_gen", v),
            fg_color=BG_CARD, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 10))

        # Tool status
        self.tool_status_label = ctk.CTkLabel(
            scale, text="Scanning tools...", text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12), justify="left"
        )
        self.tool_status_label.pack(anchor="w", padx=14, pady=(0, 8))

        btnrow = ctk.CTkFrame(scale, fg_color="transparent")
        btnrow.pack(fill="x", padx=14, pady=(0, 6))

        self.opti_btn = ctk.CTkButton(
            btnrow, text="Download OptiScaler",
            height=36, fg_color=GREEN, hover_color=GREEN_HOVER,
            command=self.download_optiscaler
        )
        self.opti_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btnrow, text="Open Folder", height=36,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            command=self.open_optiscaler_folder
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.lossless_btn = ctk.CTkButton(
            scale, text="Launch Lossless Scaling",
            height=36, fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self.launch_lossless
        )
        self.lossless_btn.pack(fill="x", padx=14, pady=(0, 14))

        # ===== MAPPER =====
        self._section("BUTTONS & MAPPER")
        mapper = self._card()

        ctk.CTkLabel(
            mapper,
            text="Recommended duties:\n"
                 "• Left Legion button  → Open this app\n"
                 "• Right Legion button → Open Quick Menu",
            justify="left", text_color=TEXT, font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkLabel(
            mapper,
            text="Map the physical buttons with PowerToys\nor AutoHotkey so they open this app",
            justify="left", text_color=TEXT_DIM, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self.mapper_var = ctk.StringVar(value=self.config.get("mapper_profile", "Default"))
        ctk.CTkOptionMenu(
            mapper,
            values=["Default", "Desktop", "FPS", "Racing", "Custom 1", "Custom 2"],
            variable=self.mapper_var,
            command=lambda v: self.update_config("mapper_profile", v),
            fg_color=BG_CARD, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ===== DRIVERS =====
        self._section("DRIVERS")
        drivers = self._card()

        ctk.CTkLabel(
            drivers,
            text="Official AMD Adrenalin for Legion Go\nVersion 25.30.44",
            justify="left", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT
        ).pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkButton(
            drivers, text="Download AMD 25.30.44",
            height=40, font=ctk.CTkFont(weight="bold"),
            fg_color=ORANGE, hover_color="#d35400",
            command=lambda: webbrowser.open(LENOVO_AMD_DRIVER_URL)
        ).pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(
            drivers, text="Lenovo Support Page", height=34,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            command=lambda: webbrowser.open(LENOVO_SUPPORT_URL)
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ===== UPDATES =====
        self._section("APP UPDATES")
        upd = self._card()

        self.version_label = ctk.CTkLabel(
            upd, text=f"Current version: {APP_VERSION}",
            font=ctk.CTkFont(size=13), text_color=TEXT
        )
        self.version_label.pack(anchor="w", padx=14, pady=(12, 4))

        self.update_status = ctk.CTkLabel(
            upd, text="", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)
        )
        self.update_status.pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkButton(
            upd, text="Check & Update from GitHub",
            height=40, font=ctk.CTkFont(weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self.check_and_update
        ).pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(
            upd, text="Open GitHub Page", height=34,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            command=lambda: webbrowser.open(GITHUB_PAGE)
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ===== SYSTEM =====
        self._section("SYSTEM")
        sysf = self._card()

        self.sys_info = ctk.CTkLabel(
            sysf, text="Loading...", justify="left",
            font=ctk.CTkFont(size=13), text_color=TEXT
        )
        self.sys_info.pack(anchor="w", padx=14, pady=12)

        ctk.CTkButton(
            sysf, text="Refresh", height=32,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            command=self.update_sys_info
        ).pack(fill="x", padx=14, pady=(0, 14))

        self.after(400, self.update_sys_info)

    def _section(self, text):
        ctk.CTkLabel(
            self.panel_scroll, text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(16, 4), padx=4)

    def _card(self):
        f = ctk.CTkFrame(self.panel_scroll, fg_color=BG_CARD, corner_radius=12)
        f.pack(fill="x", pady=(0, 4))
        return f

    # ------------------------------------------------------------------
    # Panel show/hide
    # ------------------------------------------------------------------
    def toggle_right_panel(self):
        if self.right_panel_visible:
            self.hide_right_panel()
        else:
            self.show_right_panel()

    def show_right_panel(self):
        self.right_panel.grid()
        self.right_panel_visible = True
        self.menu_btn.configure(text="Close Menu  ◀")

    def hide_right_panel(self):
        self.right_panel.grid_remove()
        self.right_panel_visible = False
        self.menu_btn.configure(text="Quick Menu  ▶")

    # ------------------------------------------------------------------
    # Force Close Legion Space
    # ------------------------------------------------------------------
    def force_close_legion_space(self):
        killed = []
        if psutil:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    name = proc.info["name"]
                    if name and name.lower() in [p.lower() for p in LEGION_SPACE_PROCESSES]:
                        proc.kill()
                        killed.append(name)
                except Exception:
                    pass
        else:
            for name in LEGION_SPACE_PROCESSES:
                try:
                    r = subprocess.run(
                        ["taskkill", "/F", "/IM", name],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    if r.returncode == 0:
                        killed.append(name)
                except Exception:
                    pass

        if killed:
            self.ls_status.configure(
                text=f"Closed: {', '.join(sorted(set(killed)))}",
                text_color=GREEN
            )
        else:
            self.ls_status.configure(text="No Legion Space processes found", text_color=TEXT_MUTED)

    # ------------------------------------------------------------------
    # Tool scanning
    # ------------------------------------------------------------------
    def find_lossless_scaling(self):
        candidates = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam" / "steamapps" / "common" / "Lossless Scaling" / "LosslessScaling.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam" / "steamapps" / "common" / "Lossless Scaling" / "LosslessScaling.exe",
        ]
        # Also check common library folders
        for drive in "CDEF":
            p = Path(f"{drive}:/SteamLibrary/steamapps/common/Lossless Scaling/LosslessScaling.exe")
            candidates.append(p)
            p2 = Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe")
            candidates.append(p2)

        for p in candidates:
            if p.exists():
                return p
        return None

    def refresh_tool_status(self):
        lines = []

        # OptiScaler
        if OPTISCALER_DIR.exists() and any(OPTISCALER_DIR.iterdir()):
            lines.append("OptiScaler: Installed")
            self.opti_btn.configure(text="Update OptiScaler")
        else:
            lines.append("OptiScaler: Not installed")
            self.opti_btn.configure(text="Download OptiScaler")

        # Lossless Scaling
        ls = self.find_lossless_scaling()
        if ls:
            lines.append("Lossless Scaling: Found")
            self.lossless_btn.configure(text="Launch Lossless Scaling", state="normal")
        else:
            lines.append("Lossless Scaling: Not found")
            self.lossless_btn.configure(text="Lossless Scaling (not installed)")

        # RyzenAdj
        ryzen = any([
            (APP_DIR / "ryzenadj.exe").exists(),
            Path("C:/tools/ryzenadj/ryzenadj.exe").exists(),
        ])
        lines.append("RyzenAdj: " + ("Found" if ryzen else "Not found"))

        self.tool_status_label.configure(text="\n".join(lines))

    # ------------------------------------------------------------------
    # OptiScaler download
    # ------------------------------------------------------------------
    def download_optiscaler(self):
        if self.download_in_progress:
            return
        self.download_in_progress = True
        self.opti_btn.configure(text="Downloading...", state="disabled")

        def worker():
            try:
                api = "https://api.github.com/repos/optiscaler/OptiScaler/releases/latest"
                req = urllib.request.Request(api, headers={"User-Agent": "Legion-Custom-App"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode())

                tag = data.get("tag_name", "?")
                zip_url = None
                for a in data.get("assets", []):
                    if a.get("name", "").lower().endswith(".zip"):
                        zip_url = a["browser_download_url"]
                        break
                if not zip_url:
                    zip_url = data.get("zipball_url")

                with tempfile.TemporaryDirectory() as tmp:
                    zpath = Path(tmp) / "opti.zip"
                    urllib.request.urlretrieve(zip_url, zpath)
                    extract = Path(tmp) / "out"
                    extract.mkdir()
                    with zipfile.ZipFile(zpath) as zf:
                        zf.extractall(extract)

                    if OPTISCALER_DIR.exists():
                        shutil.rmtree(OPTISCALER_DIR)
                    OPTISCALER_DIR.mkdir()

                    items = list(extract.iterdir())
                    src = items[0] if len(items) == 1 and items[0].is_dir() else extract
                    for item in src.iterdir():
                        dest = OPTISCALER_DIR / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)

                self.after(0, lambda: self.tool_status_label.configure(
                    text=f"OptiScaler {tag} installed\n" + self.tool_status_label.cget("text").split("\n", 1)[-1]
                ))
            except Exception as e:
                print("OptiScaler error:", e)
                self.after(0, lambda: self.tool_status_label.configure(text=f"Download failed: {e}"))
            finally:
                self.download_in_progress = False
                self.after(0, lambda: self.opti_btn.configure(state="normal"))
                self.after(0, self.refresh_tool_status)

        threading.Thread(target=worker, daemon=True).start()

    def open_optiscaler_folder(self):
        OPTISCALER_DIR.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OPTISCALER_DIR)

    def launch_lossless(self):
        path = self.find_lossless_scaling()
        if path:
            subprocess.Popen([str(path)])
        else:
            # Try Steam protocol
            try:
                subprocess.Popen(["cmd", "/c", "start", "steam://rungameid/993090"], shell=True)
            except Exception:
                self.tool_status_label.configure(text="Lossless Scaling not found. Install from Steam.")

    # ------------------------------------------------------------------
    # In-app updater
    # ------------------------------------------------------------------
    def check_and_update(self):
        if self.update_in_progress:
            return
        self.update_in_progress = True
        self.update_status.configure(text="Checking GitHub...", text_color=TEXT_DIM)

        def worker():
            try:
                files_to_update = ["main.py", "requirements.txt", "README.md", "install.bat", "run.bat"]
                updated = []

                for fname in files_to_update:
                    url = f"{GITHUB_RAW}/{fname}"
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent": "Legion-Custom-App"})
                        with urllib.request.urlopen(req, timeout=20) as r:
                            content = r.read()
                        target = APP_DIR / fname
                        # Only write if different or missing
                        if not target.exists() or target.read_bytes() != content:
                            target.write_bytes(content)
                            updated.append(fname)
                    except Exception as e:
                        print(f"Could not update {fname}:", e)

                if updated:
                    msg = f"Updated: {', '.join(updated)}. Restarting..."
                    self.after(0, lambda: self.update_status.configure(text=msg, text_color=GREEN))
                    time.sleep(1.5)
                    # Restart
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)
                else:
                    self.after(0, lambda: self.update_status.configure(
                        text="Already up to date", text_color=GREEN
                    ))
            except Exception as e:
                self.after(0, lambda: self.update_status.configure(
                    text=f"Update failed: {e}", text_color=RED
                ))
            finally:
                self.update_in_progress = False

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Performance helpers
    # ------------------------------------------------------------------
    def on_preset_change(self):
        preset = self.preset_var.get()
        self.update_config("preset", preset)
        mapping = {"Quiet": 15, "Balanced": 25, "Performance": 35}
        if preset in mapping:
            tdp = mapping[preset]
            self.tdp_slider.set(tdp)
            self.tdp_label.configure(text=f"{tdp} W")
            self.update_config("tdp", tdp)

    def on_tdp_change(self, v):
        val = int(float(v))
        self.tdp_label.configure(text=f"{val} W")
        self.update_config("tdp", val)
        self.preset_var.set("Custom")

    def apply_tdp(self):
        tdp = int(self.config.get("tdp", 25))
        candidates = [
            APP_DIR / "ryzenadj.exe",
            Path("C:/tools/ryzenadj/ryzenadj.exe"),
        ]
        ryzen = next((c for c in candidates if c.exists()), None)
        if ryzen:
            try:
                cmd = [str(ryzen), f"--stapm-limit={tdp*1000}", f"--fast-limit={tdp*1000}", f"--slow-limit={tdp*1000}"]
                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                subprocess.Popen(cmd, creationflags=flags)
            except Exception as e:
                print(e)
        else:
            print(f"[Placeholder] TDP {tdp}W - place ryzenadj.exe next to the app")

    def update_sys_info(self):
        lines = [f"Version: {APP_VERSION}"]
        if psutil:
            try:
                lines.append(f"CPU: {psutil.cpu_percent(interval=0.15):.0f}%")
                mem = psutil.virtual_memory()
                lines.append(f"RAM: {mem.percent:.0f}%")
            except Exception:
                pass
        lines.append(f"Preset: {self.config.get('preset')}")
        lines.append(f"Scaler: {self.config.get('scaler')}")
        lines.append(f"Frame Gen: {self.config.get('frame_gen')}")
        self.sys_info.configure(text="\n".join(lines))

    # ------------------------------------------------------------------
    # Games
    # ------------------------------------------------------------------
    def refresh_games(self):
        for w in self.games_scroll.winfo_children():
            w.destroy()
        self.games = self.scan_games()

        if not self.games:
            ctk.CTkLabel(
                self.games_scroll,
                text="No games found.\nSteam libraries are scanned automatically.",
                text_color=TEXT_MUTED, font=ctk.CTkFont(size=14)
            ).grid(row=0, column=0, columnspan=4, pady=60)
            return

        for i, g in enumerate(self.games):
            r, c = divmod(i, 4)
            card = self._game_card(g)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

    def _game_card(self, game):
        f = ctk.CTkFrame(self.games_scroll, width=220, height=130, corner_radius=14, fg_color=BG_CARD)
        f.grid_propagate(False)

        name = game.get("name", "?")[:28]
        ctk.CTkLabel(
            f, text=name, font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT, wraplength=200
        ).pack(pady=(20, 10), padx=10)

        path = game.get("path")
        if path and Path(path).exists():
            ctk.CTkButton(
                f, text="Play", width=100, height=32,
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                command=lambda p=path: self.launch_game(p)
            ).pack()
        return f

    def launch_game(self, path):
        try:
            if str(path).lower().endswith(".exe"):
                subprocess.Popen([path], cwd=str(Path(path).parent))
            else:
                os.startfile(path)
        except Exception as e:
            print(e)

    def scan_games(self):
        found = []
        bases = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam" / "steamapps" / "common",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam" / "steamapps" / "common",
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

        return list({g["name"]: g for g in found}.values())[:48]


if __name__ == "__main__":
    app = LegionCustomApp()
    app.mainloop()

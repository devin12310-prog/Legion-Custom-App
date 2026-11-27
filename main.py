#!/usr/bin/env python3
"""Legion Custom App v1.4.0"""

import customtkinter as ctk
import subprocess, os, sys, webbrowser, json, threading, time, shutil, tempfile, zipfile
from pathlib import Path
import urllib.request

try:
    import psutil
except ImportError:
    psutil = None

APP_NAME = "Legion Custom"
APP_VERSION = "1.4.0"
GITHUB_REPO = "devin12310-prog/Legion-Custom-App"
GITHUB_PAGE = f"https://github.com/{GITHUB_REPO}"
GITHUB_ZIP = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"

APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "config.json"
OPTISCALER_DIR = APP_DIR / "OptiScaler"

LENOVO_AMD_DRIVER_URL = "https://support.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1/downloads/ds565497-amd-graphics-driver-for-windows-11-64-bit-legion-go-8apu1"

LEGION_SPACE_PROCESSES = [
    "LegionSpace.exe", "LSDaemon.exe", "LegionSettingMenu.exe",
    "LegionGameWidget.exe", "LegionGameWidget_Sub.exe",
    "LegionSpaceComponent.exe", "LegionSpaceToast.exe",
]

DEFAULT_CONFIG = {
    "tdp": 25, "preset": "Balanced", "fan_mode": "Smart",
    "scaler": "None", "frame_gen": "Off",
    "resolution": "1600x1000", "refresh": 144,
}

BG, PANEL, CARD = "#0d1117", "#161b22", "#1c2333"
ACCENT, ACCENT_DIM = "#00d2a0", "#00a87e"
BLUE, RED, ORANGE = "#3d7eff", "#ff4757", "#ffa502"
TEXT, TEXT_DIM, TEXT_MUTED = "#e6edf3", "#8b949e", "#484f58"
PILL = "#21262d"

ctk.set_appearance_mode("dark")


class LegionCustomApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        # Larger default for Legion Go screen
        self.geometry("1600x1000")
        self.minsize(1200, 800)
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)
        self.after(400, lambda: self.attributes("-topmost", False))

        self.config = self._load()
        self.menu_open = False
        self.busy = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # right panel fixed
        self.grid_rowconfigure(0, weight=1)

        self._build_main()
        self._build_menu()

        self.bind("<Control-Shift-L>", lambda e: self.toggle_menu())
        self.bind("<F1>", lambda e: self.toggle_menu())
        self.bind("<Escape>", lambda e: self.close_menu())

        if "--menu" in sys.argv:
            self.after(250, self.open_menu)

        self.after(300, self.refresh_games)
        self.after(500, self.refresh_tools)
        self.after(800, self._stats_loop)

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text())}
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def _save(self):
        try:
            CONFIG_FILE.write_text(json.dumps(self.config, indent=2))
        except Exception:
            pass

    def setc(self, k, v):
        self.config[k] = v
        self._save()

    # ================= MAIN =================
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.main, height=72, fg_color=PANEL, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        ctk.CTkLabel(top, text="LEGION CUSTOM",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT).pack(side="left", padx=24, pady=18)
        ctk.CTkLabel(top, text=f"v{APP_VERSION}", font=ctk.CTkFont(size=13),
                     text_color=TEXT_MUTED).pack(side="left")

        self.menu_btn = ctk.CTkButton(
            top, text="Quick Menu  ▶", width=170, height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
            command=self.toggle_menu
        )
        self.menu_btn.pack(side="right", padx=20)

        body = ctk.CTkFrame(self.main, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(body, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(hdr, text="Games", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="Refresh", width=100, height=34, fg_color=CARD,
                      command=self.refresh_games).pack(side="right")

        self.games_scroll = ctk.CTkScrollableFrame(body, fg_color=PANEL, corner_radius=16)
        self.games_scroll.grid(row=1, column=0, sticky="nsew")
        self.games_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

    # ================= QUICK MENU =================
    def _build_menu(self):
        # Wider panel for Legion Go
        self.menu = ctk.CTkFrame(self, width=460, fg_color=PANEL, corner_radius=0)
        self.menu.grid(row=0, column=1, sticky="nsew")
        self.menu.grid_propagate(False)
        # Start hidden
        self.menu.grid_remove()

        hdr = ctk.CTkFrame(self.menu, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(hdr, text="QUICK MENU", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="✕", width=40, height=40, fg_color="transparent",
                      hover_color=CARD, font=ctk.CTkFont(size=16),
                      command=self.close_menu).pack(side="right")

        self.ms = ctk.CTkScrollableFrame(self.menu, fg_color="transparent")
        self.ms.pack(fill="both", expand=True, padx=14, pady=4)

        # FORCE CLOSE
        self._sec("LEGION SPACE")
        fc = self._card()
        ctk.CTkButton(fc, text="FORCE CLOSE LEGION SPACE", height=48,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=RED, hover_color="#e03e4e",
                      command=self.force_close).pack(fill="x", padx=14, pady=(14, 6))
        self.fc_status = ctk.CTkLabel(fc, text="Ready", text_color=TEXT_MUTED)
        self.fc_status.pack(anchor="w", padx=14, pady=(0, 14))

        # PERFORMANCE
        self._sec("PERFORMANCE")
        perf = self._card()
        row = ctk.CTkFrame(perf, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(14, 10))
        self.mode_btns = {}
        for key, label in [("Performance", "High Perf"), ("Quiet", "Power Save"), ("Custom", "Custom")]:
            b = ctk.CTkButton(row, text=label, height=44, font=ctk.CTkFont(size=13, weight="bold"),
                              fg_color=PILL, command=lambda k=key: self.set_mode(k))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.mode_btns[key] = b
        self._hl_mode()

        stats = ctk.CTkFrame(perf, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=(0, 14))
        self.stat_lbls = {}
        for k, n in [("cpu", "CPU"), ("gpu", "GPU"), ("vram", "VRAM"), ("ram", "RAM")]:
            box = ctk.CTkFrame(stats, fg_color=PILL, corner_radius=12)
            box.pack(side="left", expand=True, fill="x", padx=3)
            self.stat_lbls[k] = ctk.CTkLabel(box, text="--%", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT)
            self.stat_lbls[k].pack(pady=(12, 0))
            ctk.CTkLabel(box, text=n, font=ctk.CTkFont(size=12), text_color=TEXT_DIM).pack(pady=(0, 12))

        # TDP
        self._sec("TDP / THERMAL")
        tdpf = self._card()
        trow = ctk.CTkFrame(tdpf, fg_color="transparent")
        trow.pack(fill="x", padx=12, pady=(14, 8))
        self.tdp_btns = {}
        for key in ["Quiet", "Balanced", "Performance", "Custom"]:
            b = ctk.CTkButton(trow, text=key, height=38, font=ctk.CTkFont(size=12),
                              fg_color=PILL, command=lambda k=key: self.set_tdp_mode(k))
            b.pack(side="left", expand=True, fill="x", padx=2)
            self.tdp_btns[key] = b
        self._hl_tdp()

        self.tdp_slider = ctk.CTkSlider(tdpf, from_=8, to=40, number_of_steps=32,
                                        progress_color=ACCENT, button_color=ACCENT, command=self.on_tdp)
        self.tdp_slider.set(self.config.get("tdp", 25))
        self.tdp_slider.pack(fill="x", padx=16, pady=(8, 4))
        self.tdp_val = ctk.CTkLabel(tdpf, text=f"{int(self.config.get('tdp',25))} W",
                                    font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT)
        self.tdp_val.pack(pady=(0, 6))
        ctk.CTkButton(tdpf, text="Apply TDP", height=40, fg_color=ACCENT, hover_color=ACCENT_DIM,
                      text_color="#000", font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.apply_tdp).pack(fill="x", padx=14, pady=(0, 14))

        # FAN
        self._sec("FAN")
        fanf = self._card()
        frow = ctk.CTkFrame(fanf, fg_color="transparent")
        frow.pack(fill="x", padx=12, pady=(14, 10))
        self.fan_btns = {}
        for key, label in [("Smart", "Smart"), ("Full", "Full Speed")]:
            b = ctk.CTkButton(frow, text=label, height=42, font=ctk.CTkFont(size=14, weight="bold"),
                              fg_color=PILL, command=lambda k=key: self.set_fan(k))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.fan_btns[key] = b
        self._hl_fan()
        self.fan_canvas = ctk.CTkCanvas(fanf, height=100, bg=PILL, highlightthickness=0)
        self.fan_canvas.pack(fill="x", padx=14, pady=(0, 14))
        self.after(200, self.draw_fan)

        # DISPLAY
        self._sec("DISPLAY")
        disp = self._card()
        ctk.CTkLabel(disp, text="Resolution", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(14, 6))
        rrow = ctk.CTkFrame(disp, fg_color="transparent")
        rrow.pack(fill="x", padx=10, pady=(0, 10))
        self.res_btns = {}
        for res in ["1280x800", "1600x1000", "1920x1200"]:
            b = ctk.CTkButton(rrow, text=res, height=38, font=ctk.CTkFont(size=12),
                              fg_color=PILL, command=lambda r=res: self.set_res(r))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.res_btns[res] = b
        self._hl_res()

        ctk.CTkLabel(disp, text="Refresh Rate", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(4, 6))
        hzrow = ctk.CTkFrame(disp, fg_color="transparent")
        hzrow.pack(fill="x", padx=10, pady=(0, 14))
        self.ref_btns = {}
        for hz in [60, 144]:
            b = ctk.CTkButton(hzrow, text=f"{hz} Hz", height=38, font=ctk.CTkFont(size=13, weight="bold"),
                              fg_color=PILL, command=lambda h=hz: self.set_ref(h))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.ref_btns[hz] = b
        self._hl_ref()

        # ===== UPSCALER (restored) =====
        self._sec("UPSCALER")
        upsf = self._card()
        ctk.CTkLabel(upsf, text="Select upscaler for games", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(14, 6))
        self.scaler_var = ctk.StringVar(value=self.config.get("scaler", "None"))
        ctk.CTkOptionMenu(
            upsf,
            values=["None", "FSR 2 / 3 / 4", "XeSS", "OptiScaler (Auto)", "DLSS Spoof"],
            variable=self.scaler_var,
            command=lambda v: self.setc("scaler", v),
            height=40, font=ctk.CTkFont(size=14),
            fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ===== FRAME GEN (restored) =====
        self._sec("FRAME GENERATION")
        fgf = self._card()
        ctk.CTkLabel(fgf, text="Select frame generation method", text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(14, 6))
        self.fg_var = ctk.StringVar(value=self.config.get("frame_gen", "Off"))
        ctk.CTkOptionMenu(
            fgf,
            values=["Off", "Lossless Scaling (LSFG)", "AMD AFMF", "OptiFG", "XeFG"],
            variable=self.fg_var,
            command=lambda v: self.setc("frame_gen", v),
            height=40, font=ctk.CTkFont(size=14),
            fg_color=PILL, button_color=ACCENT
        ).pack(fill="x", padx=14, pady=(0, 10))

        self.fg_status = ctk.CTkLabel(fgf, text="Checking Lossless Scaling...", text_color=TEXT_DIM,
                                      font=ctk.CTkFont(size=12))
        self.fg_status.pack(anchor="w", padx=14, pady=(0, 6))

        self.lossless_btn = ctk.CTkButton(fgf, text="Launch Lossless Scaling", height=42,
                                          font=ctk.CTkFont(size=14, weight="bold"),
                                          fg_color=BLUE, hover_color="#2a5fd4",
                                          command=self.launch_lossless)
        self.lossless_btn.pack(fill="x", padx=14, pady=(0, 14))

        # ===== OPTISCALER TOOL =====
        self._sec("OPTISCALER TOOL")
        opt = self._card()
        self.opti_status = ctk.CTkLabel(opt, text="Checking...", text_color=TEXT_DIM,
                                        font=ctk.CTkFont(size=12))
        self.opti_status.pack(anchor="w", padx=14, pady=(14, 8))

        orow = ctk.CTkFrame(opt, fg_color="transparent")
        orow.pack(fill="x", padx=12, pady=(0, 6))
        self.opti_dl_btn = ctk.CTkButton(orow, text="Download / Update", height=40,
                                         fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
                                         command=self.download_optiscaler)
        self.opti_dl_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(orow, text="Folder", width=80, height=40, fg_color=PILL,
                      command=self.open_opti_folder).pack(side="left", padx=(0, 4))
        ctk.CTkButton(orow, text="Remove", width=80, height=40, fg_color=RED,
                      command=self.remove_optiscaler).pack(side="left")
        ctk.CTkLabel(opt, text="Copy files into game folder (rename to dxgi.dll)",
                     text_color=TEXT_MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=14, pady=(4, 14))

        # DRIVERS
        self._sec("DRIVERS")
        dr = self._card()
        ctk.CTkButton(dr, text="AMD Adrenalin 25.30.44 (Legion Go)", height=46,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=ORANGE, hover_color="#e69500",
                      command=lambda: webbrowser.open(LENOVO_AMD_DRIVER_URL)).pack(fill="x", padx=14, pady=14)

        # UPDATES
        self._sec("APP UPDATES")
        up = self._card()
        self.upd_status = ctk.CTkLabel(up, text=f"Current version: {APP_VERSION}",
                                       text_color=TEXT_DIM, font=ctk.CTkFont(size=13))
        self.upd_status.pack(anchor="w", padx=14, pady=(14, 8))
        self.upd_btn = ctk.CTkButton(up, text="Check & Update from GitHub", height=46,
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
                                     command=self.do_update)
        self.upd_btn.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkButton(up, text="Open GitHub Page", height=38, fg_color=PILL,
                      command=lambda: webbrowser.open(GITHUB_PAGE)).pack(fill="x", padx=14, pady=(0, 14))

    def _sec(self, t):
        ctk.CTkLabel(self.ms, text=t, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_MUTED, anchor="w").pack(fill="x", pady=(20, 6), padx=2)

    def _card(self):
        f = ctk.CTkFrame(self.ms, fg_color=CARD, corner_radius=14)
        f.pack(fill="x", pady=(0, 6))
        return f

    # ---------- menu open/close (fixed) ----------
    def toggle_menu(self):
        if self.menu_open:
            self.close_menu()
        else:
            self.open_menu()

    def open_menu(self):
        self.menu.grid()
        self.menu_open = True
        self.menu_btn.configure(text="Close Menu  ◀")
        self.update_idletasks()
        self.draw_fan()

    def close_menu(self):
        self.menu.grid_remove()
        self.menu_open = False
        self.menu_btn.configure(text="Quick Menu  ▶")

    # ---------- helpers ----------
    def _hl(self, btns, cur):
        for k, b in btns.items():
            b.configure(fg_color=ACCENT if k == cur else PILL,
                        text_color="#000" if k == cur else TEXT)

    def _hl_mode(self):
        cur = self.config.get("preset", "Balanced")
        self._hl(self.mode_btns, "Custom" if cur == "Balanced" else cur)

    def _hl_tdp(self):
        self._hl(self.tdp_btns, self.config.get("preset", "Balanced"))

    def _hl_fan(self):
        self._hl(self.fan_btns, self.config.get("fan_mode", "Smart"))

    def _hl_res(self):
        self._hl(self.res_btns, self.config.get("resolution", "1600x1000"))

    def _hl_ref(self):
        self._hl(self.ref_btns, int(self.config.get("refresh", 144)))

    def set_mode(self, key):
        m = {"Performance": 35, "Quiet": 15, "Custom": self.config.get("tdp", 25)}
        self.setc("preset", key)
        t = m.get(key, 25)
        self.tdp_slider.set(t)
        self.tdp_val.configure(text=f"{t} W")
        self.setc("tdp", t)
        self._hl_mode(); self._hl_tdp()

    def set_tdp_mode(self, key):
        m = {"Quiet": 15, "Balanced": 25, "Performance": 35}
        self.setc("preset", key)
        if key in m:
            self.tdp_slider.set(m[key])
            self.tdp_val.configure(text=f"{m[key]} W")
            self.setc("tdp", m[key])
        self._hl_tdp(); self._hl_mode()

    def on_tdp(self, v):
        val = int(float(v))
        self.tdp_val.configure(text=f"{val} W")
        self.setc("tdp", val)
        self.setc("preset", "Custom")
        self._hl_tdp(); self._hl_mode()

    def set_fan(self, key):
        self.setc("fan_mode", key)
        self._hl_fan()
        self.draw_fan()

    def set_res(self, r):
        self.setc("resolution", r)
        self._hl_res()

    def set_ref(self, h):
        self.setc("refresh", h)
        self._hl_ref()

    def draw_fan(self):
        c = self.fan_canvas
        c.delete("all")
        w = max(c.winfo_width(), 360)
        h = 100
        for i in range(1, 5):
            c.create_line(12, h - i * h / 5, w - 12, h - i * h / 5, fill="#2a303c")
        mode = self.config.get("fan_mode", "Smart")
        pts = [(0, .9), (.3, .95), (1, 1)] if mode == "Full" else [(0, .15), (.3, .3), (.6, .55), (1, .95)]
        coords = []
        for x, y in pts:
            coords += [12 + x * (w - 24), h - 10 - y * (h - 24)]
        if len(coords) >= 4:
            c.create_line(*coords, fill=ACCENT, width=3, smooth=True)
            for i in range(0, len(coords), 2):
                c.create_oval(coords[i]-4, coords[i+1]-4, coords[i]+4, coords[i+1]+4, fill=ACCENT, outline="")

    def force_close(self):
        killed = []
        if psutil:
            for p in psutil.process_iter(["name"]):
                try:
                    n = p.info["name"]
                    if n and n.lower() in [x.lower() for x in LEGION_SPACE_PROCESSES]:
                        p.kill(); killed.append(n)
                except Exception:
                    pass
        else:
            for name in LEGION_SPACE_PROCESSES:
                try:
                    r = subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True,
                                       creationflags=0x08000000 if sys.platform == "win32" else 0)
                    if r.returncode == 0: killed.append(name)
                except Exception:
                    pass
        if killed:
            self.fc_status.configure(text=f"Closed: {', '.join(sorted(set(killed)))}", text_color=ACCENT)
        else:
            self.fc_status.configure(text="No Legion Space processes running", text_color=TEXT_MUTED)

    def _stats_loop(self):
        if psutil:
            try:
                self.stat_lbls["cpu"].configure(text=f"{psutil.cpu_percent(interval=None):.0f}%")
                self.stat_lbls["ram"].configure(text=f"{psutil.virtual_memory().percent:.0f}%")
            except Exception:
                pass
        self.after(2000, self._stats_loop)

    def find_lossless(self):
        cands = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/steamapps/common/Lossless Scaling/LosslessScaling.exe",
        ]
        for d in "CDEF":
            cands.append(Path(f"{d}:/SteamLibrary/steamapps/common/Lossless Scaling/LosslessScaling.exe"))
        for p in cands:
            if p.exists(): return p
        return None

    def refresh_tools(self):
        if OPTISCALER_DIR.exists() and any(OPTISCALER_DIR.iterdir()):
            self.opti_status.configure(text="Status: Installed", text_color=ACCENT)
            self.opti_dl_btn.configure(text="Update OptiScaler")
        else:
            self.opti_status.configure(text="Status: Not installed", text_color=TEXT_DIM)
            self.opti_dl_btn.configure(text="Download OptiScaler")

        ls = self.find_lossless()
        if ls:
            self.fg_status.configure(text="Lossless Scaling: Found", text_color=ACCENT)
            self.lossless_btn.configure(text="Launch Lossless Scaling", state="normal")
        else:
            self.fg_status.configure(text="Lossless Scaling: Not found (Steam)", text_color=TEXT_DIM)

    def download_optiscaler(self):
        if self.busy: return
        self.busy = True
        self.opti_dl_btn.configure(text="Downloading...", state="disabled")
        self.opti_status.configure(text="Downloading...", text_color=ORANGE)

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
                self.after(0, lambda: self.opti_status.configure(text=f"Installed {tag}", text_color=ACCENT))
            except Exception as e:
                self.after(0, lambda: self.opti_status.configure(text=f"Failed: {e}", text_color=RED))
            finally:
                self.busy = False
                self.after(0, lambda: self.opti_dl_btn.configure(state="normal"))
                self.after(0, self.refresh_tools)

        threading.Thread(target=work, daemon=True).start()

    def open_opti_folder(self):
        OPTISCALER_DIR.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OPTISCALER_DIR)

    def remove_optiscaler(self):
        if OPTISCALER_DIR.exists():
            try:
                shutil.rmtree(OPTISCALER_DIR)
                self.opti_status.configure(text="Removed", text_color=TEXT_DIM)
            except Exception as e:
                self.opti_status.configure(text=f"Remove failed: {e}", text_color=RED)
        self.refresh_tools()

    def launch_lossless(self):
        p = self.find_lossless()
        if p:
            subprocess.Popen([str(p)])
        else:
            try:
                subprocess.Popen(["cmd", "/c", "start", "steam://rungameid/993090"], shell=True)
            except Exception:
                self.fg_status.configure(text="Install Lossless Scaling from Steam", text_color=RED)

    def apply_tdp(self):
        tdp = int(self.config.get("tdp", 25))
        for c in [APP_DIR / "ryzenadj.exe", Path("C:/tools/ryzenadj/ryzenadj.exe")]:
            if c.exists():
                try:
                    subprocess.Popen([str(c), f"--stapm-limit={tdp*1000}",
                                      f"--fast-limit={tdp*1000}", f"--slow-limit={tdp*1000}"],
                                     creationflags=0x08000000 if sys.platform == "win32" else 0)
                except Exception:
                    pass
                return

    def do_update(self):
        if self.busy: return
        self.busy = True
        self.upd_btn.configure(state="disabled", text="Updating...")
        self.upd_status.configure(text="Downloading from GitHub...", text_color=ORANGE)

        def work():
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    zp = Path(tmp) / "repo.zip"
                    req = urllib.request.Request(GITHUB_ZIP, headers={"User-Agent": "Legion-Custom-App"})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        zp.write_bytes(r.read())
                    extract = Path(tmp) / "out"; extract.mkdir()
                    with zipfile.ZipFile(zp) as z: z.extractall(extract)
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
                        self.after(0, lambda: self.upd_status.configure(
                            text=f"Updated: {', '.join(updated)}\nRestarting...", text_color=ACCENT))
                        time.sleep(1.5)
                        subprocess.Popen([sys.executable, str(APP_DIR / "main.py")] + sys.argv[1:], cwd=str(APP_DIR))
                        self.after(0, self.destroy)
                    else:
                        self.after(0, lambda: self.upd_status.configure(text="Already up to date", text_color=ACCENT))
            except Exception as e:
                self.after(0, lambda: self.upd_status.configure(
                    text=f"Failed: {e}\nDownload ZIP manually from GitHub", text_color=RED))
            finally:
                self.busy = False
                self.after(0, lambda: self.upd_btn.configure(state="normal", text="Check & Update from GitHub"))

        threading.Thread(target=work, daemon=True).start()

    def refresh_games(self):
        for w in self.games_scroll.winfo_children():
            w.destroy()
        games = self.scan_games()
        if not games:
            ctk.CTkLabel(self.games_scroll, text="No games found", text_color=TEXT_MUTED).grid(
                row=0, column=0, columnspan=4, pady=60)
            return
        for i, g in enumerate(games):
            r, c = divmod(i, 4)
            card = ctk.CTkFrame(self.games_scroll, width=220, height=130, corner_radius=14, fg_color=CARD)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=g["name"][:26], font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TEXT, wraplength=200).pack(pady=(20, 10), padx=8)
            if Path(g["path"]).exists():
                ctk.CTkButton(card, text="Play", width=100, height=32,
                              fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000",
                              command=lambda p=g["path"]: subprocess.Popen([p], cwd=str(Path(p).parent))).pack()

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
        return list({g["name"]: g for g in found}.values())[:40]


if __name__ == "__main__":
    app = LegionCustomApp()
    app.mainloop()

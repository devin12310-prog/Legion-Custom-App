import customtkinter as ctk
import subprocess
import os
import sys
import webbrowser
from pathlib import Path
import json

try:
    import psutil
except ImportError:
    psutil = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

APP_DIR = Path(__file__).parent
CONFIG_FILE = APP_DIR / "config.json"

# Legion Go friendly resolutions (native + common performance options)
LEGION_RESOLUTIONS = [
    "1600x1000",   # Native
    "1280x800",
    "1920x1200",
    "1200x750",
    "800x500",
    "640x400"
]

DEFAULT_CONFIG = {
    "tdp": 25,
    "preset": "Balanced",
    "fps_limit": 0,
    "scaler": "None",
    "frame_gen": "Off",
    "resolution": "1600x1000",
    "refresh": 144,
    "brightness": 70,
    "mapper_profile": "Default",
    "start_with_menu": False
}


class LegionCustomApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Legion Custom")
        self.geometry("1280x800")
        self.minsize(1000, 600)

        # Make window appear on top when launched via Legion button
        self.attributes("-topmost", True)
        self.after(800, lambda: self.attributes("-topmost", False))

        self.config = self.load_config()
        self.right_panel_visible = False
        self.games = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===== MAIN CONTENT (Home) =====
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0f1115")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Top bar
        self.top_bar = ctk.CTkFrame(self.main_frame, height=64, corner_radius=0, fg_color="#161a22")
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.top_bar, text="LEGION CUSTOM",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left", padx=22, pady=16)

        # Right-top button that opens the Quick Menu
        self.open_menu_btn = ctk.CTkButton(
            self.top_bar, text="Quick Menu  ▶",
            width=150, height=38,
            command=self.toggle_right_panel,
            fg_color="#2a6df4", hover_color="#1e56c7",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.open_menu_btn.pack(side="right", padx=20)

        # Games area
        self.games_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.games_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        self.games_container.grid_columnconfigure(0, weight=1)
        self.games_container.grid_rowconfigure(1, weight=1)

        header_row = ctk.CTkFrame(self.games_container, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            header_row, text="Installed Games",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header_row, text="Refresh", width=90, height=30,
            command=self.refresh_games, fg_color="#2a3140"
        ).pack(side="right")

        self.games_scroll = ctk.CTkScrollableFrame(
            self.games_container, fg_color="#12151c", corner_radius=12
        )
        self.games_scroll.grid(row=1, column=0, sticky="nsew")
        self.games_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # ===== RIGHT PANEL =====
        self.right_panel = ctk.CTkFrame(self, width=400, corner_radius=0, fg_color="#161a22")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_remove()

        self.build_right_panel()

        # Hotkeys
        self.bind("<Control-Shift-L>", lambda e: self.toggle_right_panel())
        self.bind("<Escape>", lambda e: self.hide_right_panel())
        self.bind("<F1>", lambda e: self.toggle_right_panel())

        if "--menu" in sys.argv or self.config.get("start_with_menu"):
            self.after(200, self.show_right_panel)

        self.refresh_games()

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return {**DEFAULT_CONFIG, **data}
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print("Could not save config:", e)

    def update_config(self, key, value):
        self.config[key] = value
        self.save_config()

    def toggle_right_panel(self):
        if self.right_panel_visible:
            self.hide_right_panel()
        else:
            self.show_right_panel()

    def show_right_panel(self):
        self.right_panel.grid()
        self.right_panel_visible = True
        self.open_menu_btn.configure(text="Close Menu  ◀")

    def hide_right_panel(self):
        self.right_panel.grid_remove()
        self.right_panel_visible = False
        self.open_menu_btn.configure(text="Quick Menu  ▶")

    def build_right_panel(self):
        header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 6))

        ctk.CTkLabel(
            header, text="QUICK MENU",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="✕", width=34, height=34,
            fg_color="transparent", hover_color="#333",
            command=self.hide_right_panel
        ).pack(side="right")

        self.panel_scroll = ctk.CTkScrollableFrame(
            self.right_panel, fg_color="transparent"
        )
        self.panel_scroll.pack(fill="both", expand=True, padx=12, pady=6)

        # ========== 1. PERFORMANCE ==========
        self._section("PERFORMANCE")

        preset_frame = self._card()
        self.preset_var = ctk.StringVar(value=self.config.get("preset", "Balanced"))
        for name in ["Quiet", "Balanced", "Performance", "Custom"]:
            ctk.CTkRadioButton(
                preset_frame, text=name,
                variable=self.preset_var, value=name,
                command=self.on_preset_change
            ).pack(anchor="w", padx=14, pady=5)

        # TDP
        self._section("TDP LIMIT")
        tdp_frame = self._card()

        self.tdp_slider = ctk.CTkSlider(
            tdp_frame, from_=8, to=40, number_of_steps=32,
            command=self.on_tdp_change
        )
        self.tdp_slider.set(self.config.get("tdp", 25))
        self.tdp_slider.pack(fill="x", padx=14, pady=(14, 4))

        self.tdp_label = ctk.CTkLabel(tdp_frame, text=f"{int(self.config.get('tdp', 25))} W",
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self.tdp_label.pack(pady=(0, 8))

        ctk.CTkButton(
            tdp_frame, text="Apply TDP (RyzenAdj)",
            command=self.apply_tdp, fg_color="#2a6df4", height=36
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ========== 2. DISPLAY ==========
        self._section("DISPLAY")

        disp_frame = self._card()

        ctk.CTkLabel(disp_frame, text="Resolution (Legion Go)").pack(anchor="w", padx=14, pady=(12, 2))
        self.res_var = ctk.StringVar(value=self.config.get("resolution", "1600x1000"))
        ctk.CTkOptionMenu(
            disp_frame,
            values=LEGION_RESOLUTIONS,
            variable=self.res_var,
            command=lambda v: self.update_config("resolution", v)
        ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(disp_frame, text="Refresh Rate").pack(anchor="w", padx=14, pady=(4, 2))
        self.refresh_var = ctk.StringVar(value=str(self.config.get("refresh", 144)))
        ctk.CTkOptionMenu(
            disp_frame,
            values=["60", "120", "144"],
            variable=self.refresh_var,
            command=lambda v: self.update_config("refresh", int(v))
        ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(disp_frame, text="Brightness").pack(anchor="w", padx=14, pady=(4, 2))
        self.brightness_slider = ctk.CTkSlider(
            disp_frame, from_=10, to=100,
            command=lambda v: self.on_brightness_change(v)
        )
        self.brightness_slider.set(self.config.get("brightness", 70))
        self.brightness_slider.pack(fill="x", padx=14, pady=(0, 14))

        # ========== 3. SCALERS & FRAME GENERATION ==========
        self._section("SCALERS & FRAME GEN")

        scale_frame = self._card()

        ctk.CTkLabel(scale_frame, text="Upscaler").pack(anchor="w", padx=14, pady=(12, 2))
        self.scaler_var = ctk.StringVar(value=self.config.get("scaler", "None"))
        ctk.CTkOptionMenu(
            scale_frame,
            values=["None", "FSR 2 / 3 / 4", "XeSS", "OptiScaler (Auto)", "DLSS Spoof"],
            variable=self.scaler_var,
            command=lambda v: self.update_config("scaler", v)
        ).pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(scale_frame, text="Frame Generation").pack(anchor="w", padx=14, pady=(4, 2))
        self.fg_var = ctk.StringVar(value=self.config.get("frame_gen", "Off"))
        ctk.CTkOptionMenu(
            scale_frame,
            values=["Off", "Lossless Scaling (LSFG)", "AMD AFMF", "OptiFG", "XeFG"],
            variable=self.fg_var,
            command=lambda v: self.update_config("frame_gen", v)
        ).pack(fill="x", padx=14, pady=(0, 12))

        # Action buttons
        btn_row1 = ctk.CTkFrame(scale_frame, fg_color="transparent")
        btn_row1.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(
            btn_row1, text="Launch Lossless Scaling",
            command=self.launch_lossless,
            fg_color="#1a8f5c", hover_color="#147a4d", height=36
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row1, text="OptiScaler Folder",
            command=self.open_optiscaler_folder, height=36
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        # Official GitHub links
        ctk.CTkLabel(
            scale_frame, text="Official Repositories",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#7a8494"
        ).pack(anchor="w", padx=14, pady=(8, 4))

        btn_row2 = ctk.CTkFrame(scale_frame, fg_color="transparent")
        btn_row2.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(
            btn_row2, text="OptiScaler GitHub",
            command=lambda: webbrowser.open("https://github.com/optiscaler/OptiScaler"),
            height=34, fg_color="#2a3140"
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row2, text="OptiScaler Releases",
            command=lambda: webbrowser.open("https://github.com/optiscaler/OptiScaler/releases"),
            height=34, fg_color="#2a3140"
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        ctk.CTkButton(
            scale_frame, text="OptiScaler Wiki (Install Guide)",
            command=lambda: webbrowser.open("https://github.com/optiscaler/OptiScaler/wiki"),
            height=34, fg_color="#2a3140"
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ========== 4. LEGION GO MAPPER ==========
        self._section("LEGION GO MAPPER")

        mapper_frame = self._card()

        ctk.CTkLabel(
            mapper_frame,
            text="Controller profiles for Legion Go\n(Y1 / Y2 / Y3 + rear buttons)",
            justify="left"
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.mapper_var = ctk.StringVar(value=self.config.get("mapper_profile", "Default"))
        ctk.CTkOptionMenu(
            mapper_frame,
            values=["Default", "Desktop", "FPS", "Racing", "Custom 1", "Custom 2"],
            variable=self.mapper_var,
            command=lambda v: self.update_config("mapper_profile", v)
        ).pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkLabel(
            mapper_frame,
            text="Y1 → Keyboard shortcut\nY2 → Mouse button\nY3 → Macro\nRear buttons → Quick actions",
            justify="left", text_color="#9aa3b2"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        ctk.CTkButton(
            mapper_frame, text="Advanced Mapper (coming soon)",
            state="disabled", height=34
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ========== 5. DRIVERS & UPDATES ==========
        self._section("DRIVERS & UPDATES")

        drivers_frame = self._card()

        ctk.CTkLabel(
            drivers_frame,
            text="Keep Legion Go drivers and tools updated",
            justify="left"
        ).pack(anchor="w", padx=14, pady=(12, 8))

        ctk.CTkButton(
            drivers_frame, text="Lenovo Legion Drivers / Support",
            command=lambda: webbrowser.open("https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/legion-series/legion-go-8apu1"),
            height=36, fg_color="#2a3140"
        ).pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(
            drivers_frame, text="AMD Adrenalin / Chipset",
            command=lambda: webbrowser.open("https://www.amd.com/en/support"),
            height=36, fg_color="#2a3140"
        ).pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(
            drivers_frame, text="Check for App Updates (GitHub)",
            command=lambda: webbrowser.open("https://github.com/devin12310-prog/Legion-Custom-App"),
            height=36, fg_color="#2a6df4"
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ========== 6. SYSTEM ==========
        self._section("SYSTEM")

        sys_frame = self._card()

        self.sys_info_label = ctk.CTkLabel(
            sys_frame, text="Loading system info...",
            justify="left", font=ctk.CTkFont(size=13)
        )
        self.sys_info_label.pack(anchor="w", padx=14, pady=12)

        ctk.CTkButton(
            sys_frame, text="Refresh System Info",
            command=self.update_sys_info, height=32
        ).pack(fill="x", padx=14, pady=(0, 14))

        self.after(400, self.update_sys_info)

    def _section(self, text: str):
        lbl = ctk.CTkLabel(
            self.panel_scroll, text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#7a8494", anchor="w"
        )
        lbl.pack(fill="x", pady=(14, 5), padx=4)

    def _card(self):
        frame = ctk.CTkFrame(self.panel_scroll, fg_color="#1c212b", corner_radius=10)
        frame.pack(fill="x", pady=(0, 6))
        return frame

    def on_preset_change(self):
        preset = self.preset_var.get()
        self.update_config("preset", preset)
        mapping = {"Quiet": 15, "Balanced": 25, "Performance": 35, "Custom": self.config.get("tdp", 25)}
        new_tdp = mapping.get(preset, 25)
        self.tdp_slider.set(new_tdp)
        self.tdp_label.configure(text=f"{int(new_tdp)} W")
        self.update_config("tdp", new_tdp)

    def on_tdp_change(self, value):
        val = int(float(value))
        self.tdp_label.configure(text=f"{val} W")
        self.update_config("tdp", val)
        self.preset_var.set("Custom")

    def on_brightness_change(self, value):
        self.update_config("brightness", int(float(value)))

    def apply_tdp(self):
        tdp = int(self.config.get("tdp", 25))
        candidates = [
            APP_DIR / "ryzenadj.exe",
            Path("C:/tools/ryzenadj/ryzenadj.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "ryzenadj" / "ryzenadj.exe"
        ]
        ryzenadj = next((c for c in candidates if c.exists()), None)

        if ryzenadj:
            try:
                cmd = [
                    str(ryzenadj),
                    f"--stapm-limit={tdp * 1000}",
                    f"--fast-limit={tdp * 1000}",
                    f"--slow-limit={tdp * 1000}"
                ]
                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                subprocess.Popen(cmd, creationflags=flags)
                print(f"Applied ~{tdp}W via RyzenAdj")
            except Exception as e:
                print("RyzenAdj error:", e)
        else:
            print(f"[Placeholder] Set TDP to {tdp}W — place ryzenadj.exe next to the app")

    def launch_lossless(self):
        possible = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam" / "steamapps" / "common" / "Lossless Scaling" / "LosslessScaling.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam" / "steamapps" / "common" / "Lossless Scaling" / "LosslessScaling.exe",
        ]
        for p in possible:
            if p.exists():
                subprocess.Popen([str(p)])
                return
        try:
            subprocess.Popen(["cmd", "/c", "start", "steam://rungameid/993090"], shell=True)
        except Exception:
            print("Could not find Lossless Scaling. Launch it from Steam.")

    def open_optiscaler_folder(self):
        folder = APP_DIR / "OptiScaler"
        folder.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def update_sys_info(self):
        lines = []
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=0.2)
                mem = psutil.virtual_memory()
                lines.append(f"CPU: {cpu:.0f}%")
                lines.append(f"RAM: {mem.percent:.0f}%  ({mem.used // (1024**3)} / {mem.total // (1024**3)} GB)")
            except Exception:
                lines.append("psutil limited")
        else:
            lines.append("Install psutil for live stats")

        lines.append(f"Preset: {self.config.get('preset')}")
        lines.append(f"Scaler: {self.config.get('scaler')}")
        lines.append(f"Frame Gen: {self.config.get('frame_gen')}")
        lines.append(f"Resolution: {self.config.get('resolution')}")

        self.sys_info_label.configure(text="\n".join(lines))

    def refresh_games(self):
        for child in self.games_scroll.winfo_children():
            child.destroy()

        self.games = self.scan_games()

        if not self.games:
            ctk.CTkLabel(
                self.games_scroll,
                text="No games found yet.\nSteam library folders are scanned automatically.",
                text_color="#7a8494"
            ).grid(row=0, column=0, columnspan=4, pady=50)
            return

        for i, game in enumerate(self.games):
            row, col = divmod(i, 4)
            card = self.create_game_card(game)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    def create_game_card(self, game):
        frame = ctk.CTkFrame(self.games_scroll, width=210, height=125, corner_radius=10, fg_color="#1c212b")
        frame.grid_propagate(False)

        name = game.get("name", "Unknown")[:30]
        ctk.CTkLabel(
            frame, text=name,
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=190
        ).pack(pady=(18, 8), padx=8)

        path = game.get("path")
        if path and Path(path).exists():
            ctk.CTkButton(
                frame, text="Launch", height=30, width=110,
                command=lambda p=path: self.launch_game(p),
                fg_color="#2a6df4"
            ).pack(pady=(0, 12))
        else:
            ctk.CTkLabel(frame, text="Path missing", text_color="#666").pack()

        return frame

    def launch_game(self, path):
        try:
            if str(path).lower().endswith(".exe"):
                subprocess.Popen([path], cwd=str(Path(path).parent))
            else:
                if sys.platform == "win32":
                    os.startfile(path)
                else:
                    subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print("Launch failed:", e)

    def scan_games(self):
        found = []
        steam_paths = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam" / "steamapps" / "common",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam" / "steamapps" / "common",
            Path.home() / ".steam" / "steam" / "steamapps" / "common",
        ]

        for base in steam_paths:
            if not base.exists():
                continue
            for game_dir in base.iterdir():
                if game_dir.is_dir():
                    exes = list(game_dir.glob("*.exe"))
                    if not exes:
                        continue
                    main_exe = next((e for e in exes if game_dir.name.lower() in e.stem.lower()), exes[0])
                    found.append({"name": game_dir.name, "path": str(main_exe)})

        unique = {g["name"]: g for g in found}
        return list(unique.values())[:48]


if __name__ == "__main__":
    app = LegionCustomApp()
    app.mainloop()

import json
import socket
import threading
import html
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

def get_app_dir():
    """
    Return the real folder the app is running from.

    Source mode:
        folder containing this .py file

    PyInstaller EXE mode:
        folder containing the .exe file

    This keeps board_settings.json and the board JSON files local to the
    folder you put the EXE in, instead of reading from PyInstaller's temp folder.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

APP_DIR = get_app_dir()
SETTINGS_PATH = APP_DIR / "board_settings.json"

DEFAULT_CONFIG = {
    "osc_ip": "127.0.0.1",
    "osc_port": 9000,
    "cooldown_seconds": 5,
    "dark_mode": True,
    "columns": 8,
    "window_width": 1280,
    "window_height": 820,
    "web_port": 8787,
    "phrases": []
}

DEFAULT_SETTINGS = {
    "dark_mode": True,
    "active_tab": 0,
    "tabs": [
        {"file": "host.json"},
        {"file": "board_2.json"},
        {"file": "board_3.json"},
        {"file": "board_4.json"},
        {"file": "board_5.json"}
    ]
}

def osc_pad(data: bytes) -> bytes:
    padding = (4 - (len(data) % 4)) % 4
    return data + (b"\x00" * padding)

def osc_string(value: str) -> bytes:
    return osc_pad(value.encode("utf-8") + b"\x00")

def build_chatbox_packet(text: str, send_immediately: bool = True) -> bytes:
    address = osc_string("/chatbox/input")
    typetag = osc_string(",sT" if send_immediately else ",sF")
    arg_text = osc_string(text)
    return address + typetag + arg_text

def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def display_name_from_file(path):
    stem = Path(path).stem
    return stem.replace("_", " ").replace("-", " ").strip() or "Board"

def load_settings():
    if SETTINGS_PATH.exists():
        try:
            settings = load_json(SETTINGS_PATH)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(settings)
            tabs = merged.get("tabs", [])
            while len(tabs) < 5:
                tabs.append({"file": f"board_{len(tabs)+1}.json"})
            merged["tabs"] = tabs[:5]
            return merged
        except Exception:
            return DEFAULT_SETTINGS.copy()
    save_json(SETTINGS_PATH, DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()

def normalise_config(config):
    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    phrases = merged.get("phrases", [])
    while len(phrases) < 64:
        phrases.append({"button_en": f"Empty {len(phrases)+1}", "button_ja": "空", "message": ""})
    merged["phrases"] = phrases[:64]
    return merged

def config_path_from_tab(tab):
    raw = tab.get("file", "host.json")
    p = Path(raw)

    if p.is_absolute():
        if p.exists():
            return p
        fallback = APP_DIR / p.name
        if fallback.exists():
            return fallback
        return fallback

    return APP_DIR / p

class PhraseBoardApp:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.active_tab = int(self.settings.get("active_tab", 0))
        self.current_config_path = config_path_from_tab(self.settings["tabs"][self.active_tab])
        self.config = self.load_current_config()

        self.osc_ip = str(self.config.get("osc_ip", "127.0.0.1"))
        self.osc_port = int(self.config.get("osc_port", 9000))
        self.cooldown_seconds = int(self.config.get("cooldown_seconds", 5))
        self.cooldown_remaining = 0
        self.last_button = None
        self.buttons = []
        self.dark_mode = bool(self.settings.get("dark_mode", self.config.get("dark_mode", True)))
        self.columns = int(self.config.get("columns", 8))
        self.web_port = int(self.config.get("web_port", 8787))
        self.remote_running = False
        self.remote_thread = None

        self.set_theme_values()
        self.build_ui()
        self.populate_grid()

    def load_current_config(self):
        if not self.current_config_path.exists():
            return normalise_config(DEFAULT_CONFIG.copy())
        return normalise_config(load_json(self.current_config_path))

    def save_current_config_runtime_settings(self):
        self.config["osc_ip"] = self.osc_ip_var.get().strip() or "127.0.0.1"
        try:
            self.config["osc_port"] = int(self.osc_port_var.get())
        except ValueError:
            self.config["osc_port"] = 9000
        try:
            self.config["cooldown_seconds"] = max(0, int(float(self.cooldown_var.get())))
        except ValueError:
            self.config["cooldown_seconds"] = 5

        if self.current_config_path.exists():
            save_json(self.current_config_path, self.config)

        self.osc_ip = self.config["osc_ip"]
        self.osc_port = self.config["osc_port"]
        self.cooldown_seconds = self.config["cooldown_seconds"]

    def save_settings(self):
        self.settings["dark_mode"] = bool(self.dark_mode)
        self.settings["active_tab"] = int(self.active_tab)
        save_json(SETTINGS_PATH, self.settings)

    def set_theme_values(self):
        if self.dark_mode:
            self.bg = "#151515"
            self.panel = "#202020"
            self.fg = "#f4f4f4"
            self.button_bg = "#303030"
            self.button_fg = "#ffffff"
            self.disabled_bg = "#4a4a4a"
            self.last_bg = "#247a3d"
            self.clear_bg = "#8b3030"
            self.clear_active = "#a84444"
            self.entry_bg = "#ffffff"
            self.entry_fg = "#000000"
            self.tab_bg = "#262626"
            self.tab_active = "#305c8b"
        else:
            # Softer grey light mode.
            self.bg = "#cfcfcf"
            self.panel = "#d9d9d9"
            self.fg = "#111111"
            self.button_bg = "#bfbfbf"
            self.button_fg = "#000000"
            self.disabled_bg = "#a8a8a8"
            self.last_bg = "#75b977"
            self.clear_bg = "#e39b9b"
            self.clear_active = "#d88787"
            self.entry_bg = "#eeeeee"
            self.entry_fg = "#000000"
            self.tab_bg = "#b7b7b7"
            self.tab_active = "#8fb0d9"

    def send_chatbox(self, text, send_immediately=True):
        packet = build_chatbox_packet(text, send_immediately)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(packet, (self.osc_ip, self.osc_port))

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"

    def get_remote_url(self):
        ip = self.local_ip_var.get().strip() if hasattr(self, "local_ip_var") else self.get_local_ip()
        try:
            port = int(self.web_port_var.get())
        except Exception:
            port = self.web_port
        return f"http://{ip}:{port}/"

    def refresh_remote_labels(self):
        if hasattr(self, "local_ip_var"):
            self.local_ip_var.set(self.get_local_ip())
        if hasattr(self, "remote_url_var"):
            self.remote_url_var.set(self.get_remote_url())

    def copy_remote_url(self):
        self.refresh_remote_labels()
        self.root.clipboard_clear()
        self.root.clipboard_append(self.remote_url_var.get())
        self.status_var.set("Remote URL copied.")

    def show_qr_window(self):
        self.refresh_remote_labels()
        url = self.remote_url_var.get()
        try:
            import qrcode
            from PIL import ImageTk
        except Exception:
            messagebox.showerror(
                "QR support missing",
                "QR code support needs these Python packages:\n\npip install qrcode pillow"
            )
            return

        qr = qrcode.QRCode(border=2, box_size=10)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        photo = ImageTk.PhotoImage(img)

        win = tk.Toplevel(self.root)
        win.title("Phone Remote QR Code")
        win.configure(bg=self.bg)
        win.resizable(False, False)

        title = tk.Label(win, text="Scan for Phone Remote", font=("Segoe UI", 14, "bold"), bg=self.bg, fg=self.fg)
        title.pack(padx=16, pady=(14, 6))

        qr_label = tk.Label(win, image=photo, bg="white")
        qr_label.image = photo
        qr_label.pack(padx=16, pady=8)

        url_label = tk.Label(win, text=url, bg=self.bg, fg=self.fg, wraplength=360)
        url_label.pack(padx=16, pady=(4, 12))

        close_btn = tk.Button(
            win,
            text="Close",
            command=win.destroy,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            width=12,
        )
        close_btn.pack(pady=(0, 14))

    def start_remote_server(self):
        if self.remote_running:
            self.refresh_remote_labels()
            self.status_var.set("Phone Remote is already running.")
            return

        try:
            from flask import Flask, redirect, request
        except Exception as e:
            messagebox.showerror(
                "Flask missing",
                "Flask is not installed for this Python environment.\n\nInstall it with:\n\npip install flask"
            )
            return

        try:
            port = int(self.web_port_var.get())
            if port < 1 or port > 65535:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid web port", "Web port must be a number from 1 to 65535.")
            return

        self.web_port = port
        self.config["web_port"] = port
        try:
            save_json(self.current_config_path, self.config)
        except Exception:
            pass

        flask_app = Flask(__name__)
        desktop_app = self

        def render_remote_page(board_idx=None):
            if board_idx is None:
                board_idx = desktop_app.active_tab
            try:
                board_idx = int(board_idx)
            except Exception:
                board_idx = desktop_app.active_tab
            board_idx = max(0, min(4, board_idx))

            if board_idx != desktop_app.active_tab:
                desktop_app.root.after(0, lambda idx=board_idx: desktop_app.switch_tab(idx))

            path = config_path_from_tab(desktop_app.settings["tabs"][board_idx])
            try:
                page_config = normalise_config(load_json(path))
            except Exception:
                page_config = normalise_config(DEFAULT_CONFIG.copy())

            board_name = html.escape(display_name_from_file(path))
            try:
                last_sent_raw = desktop_app.board_phrase_var.get() if hasattr(desktop_app, "board_phrase_var") else "Last sent: none"
            except Exception:
                last_sent_raw = "Last sent: none"
            last_sent = html.escape(last_sent_raw)
            phrases = page_config.get("phrases", [])
            prev_idx = (board_idx - 1) % 5
            next_idx = (board_idx + 1) % 5
            tab_label = f"Board {board_idx + 1} of 5"
            buttons = []
            for idx, phrase in enumerate(phrases):
                en = html.escape(str(phrase.get("button_en", "")).strip())
                ja = html.escape(str(phrase.get("button_ja", "")).strip())
                label = (en + ("<br>" if en and ja else "") + ja) or f"Empty {idx + 1}"
                buttons.append(
                    f'<form method="post" action="/send/{board_idx}/{idx}">'
                    f'<button class="btn" type="submit">{label}</button>'
                    f'</form>'
                )
            return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phone Remote</title>
<style>
*{box-sizing:border-box;}
body{font-family:Arial,sans-serif;background:#151515;color:#f4f4f4;margin:0;padding:14px;}
.topbar{display:grid;grid-template-columns:72px minmax(0,1fr) 72px;gap:10px;align-items:stretch;margin-bottom:10px;}
.arrowform{margin:0;}
.arrow{display:flex;align-items:center;justify-content:center;text-decoration:none;border:0;border-radius:14px;background:#305c8b;color:#fff;font-size:42px;font-weight:900;min-height:74px;line-height:1;width:100%;height:100%;}
.currenttab{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:14px;background:#202020;border:1px solid #444;padding:10px 8px;min-height:74px;}
.currenttab .small{font-size:13px;color:#cfcfcf;margin-bottom:3px;}
.currenttab .name{font-size:20px;font-weight:800;line-height:1.15;word-break:break-word;}
.lastsent{border-radius:10px;background:#101010;border:1px solid #333;color:#dcdcdc;text-align:center;font-size:14px;margin:0 0 12px;padding:10px;min-height:38px;word-break:break-word;}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;}
form{margin:0;}
.btn{width:100%;min-height:64px;border:0;border-radius:10px;background:#303030;color:#fff;font-size:15px;font-weight:bold;padding:8px;}
.btn:active,.arrow:active{background:#247a3d;}
@media (min-width:700px){.topbar{grid-template-columns:96px minmax(0,1fr) 96px;}.arrow{font-size:56px;min-height:86px;}.currenttab{min-height:86px;}.currenttab .name{font-size:24px;}.grid{grid-template-columns:repeat(4,minmax(0,1fr));}.btn{min-height:72px;}}
</style>
</head>
<body>
<div class="topbar">
<form class="arrowform" method="get" action="/tab/""" + str(prev_idx) + """"><button class="arrow" type="submit" aria-label="Previous board">&#9664;</button></form>
<div class="currenttab"><div class="small">Current tab """ + html.escape(tab_label) + """</div><div class="name">""" + board_name + """</div></div>
<form class="arrowform" method="get" action="/tab/""" + str(next_idx) + """"><button class="arrow" type="submit" aria-label="Next board">&#9654;</button></form>
</div>
<div class="lastsent">""" + last_sent + """</div>
<div class="grid">
""" + "\n".join(buttons) + """
</div>
</body>
</html>"""

        @flask_app.route("/", methods=["GET"])
        def remote_index():
            board_arg = request.args.get("board", None)
            return render_remote_page(board_arg)

        @flask_app.route("/tab/<int:board_idx>", methods=["GET", "POST"])
        def remote_switch_tab(board_idx):
            board_idx = max(0, min(4, board_idx))
            return render_remote_page(board_idx)

        @flask_app.route("/send/<int:board_idx>/<int:idx>", methods=["POST"])
        def remote_send(board_idx, idx):
            board_idx = max(0, min(4, board_idx))
            desktop_app.root.after(0, lambda: desktop_app.remote_click_phrase(board_idx, idx))
            return redirect(f"/tab/{board_idx}", code=303)

        def run_server():
            flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

        self.remote_thread = threading.Thread(target=run_server, daemon=True)
        self.remote_thread.start()
        self.remote_running = True
        self.remote_status_var.set("Running")
        self.refresh_remote_labels()
        self.status_var.set(f"Phone Remote running at {self.remote_url_var.get()}")

    def remote_click_phrase(self, board_idx, idx):
        if self.cooldown_remaining > 0:
            return
        if board_idx != self.active_tab:
            self.switch_tab(board_idx)
        phrases = self.config.get("phrases", [])
        if idx < 0 or idx >= len(phrases):
            return
        self.click_phrase(phrases[idx])

    def build_ui(self):
        self.root.title("Mellish\'s Multilingual Mute Soundboard v1.0.1")
        self.root.geometry(f'{self.config.get("window_width", 1280)}x{self.config.get("window_height", 820)}')
        self.root.minsize(1100, 650)
        self.root.configure(bg=self.bg)

        self.top = tk.Frame(self.root, bg=self.bg)
        self.top.pack(fill="x", padx=10, pady=(10, 4))

        title_row = tk.Frame(self.top, bg=self.bg)
        title_row.pack(fill="x")

        self.title_label = tk.Label(title_row, text="Mellish\'s Multilingual Mute Soundboard", font=("Segoe UI", 17, "bold"), bg=self.bg, fg=self.fg)
        self.title_label.pack(side="left", anchor="w")

        self.dark_button = tk.Button(
            title_row,
            text="Light Mode" if self.dark_mode else "Dark Mode",
            command=self.toggle_dark_mode,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            width=14,
        )
        self.dark_button.pack(side="right")

        self.board_title_var = tk.StringVar()
        self.board_phrase_var = tk.StringVar(value="Last sent: none")

        self.board_title_label = tk.Label(
            self.top,
            textvariable=self.board_title_var,
            font=("Segoe UI", 15, "bold"),
            bg=self.bg,
            fg=self.fg,
            anchor="center",
        )
        self.board_title_label.pack(fill="x", pady=(0, 2))

        self.board_phrase_label = tk.Label(
            self.top,
            textvariable=self.board_phrase_var,
            font=("Segoe UI", 10),
            bg=self.bg,
            fg=self.fg,
            anchor="center",
            justify="center",
            wraplength=980,
        )
        self.board_phrase_label.pack(fill="x", pady=(0, 4))

        settings_row = tk.Frame(self.top, bg=self.bg)
        settings_row.pack(fill="x", pady=(4, 0))

        tk.Label(settings_row, text="Target:", bg=self.bg, fg=self.fg).pack(side="left")
        self.osc_ip_var = tk.StringVar(value=str(self.config.get("osc_ip", "127.0.0.1")))
        self.osc_ip_entry = tk.Entry(settings_row, textvariable=self.osc_ip_var, width=15, bg=self.entry_bg, fg=self.entry_fg)
        self.osc_ip_entry.pack(side="left", padx=(4, 4))

        tk.Label(settings_row, text="Port:", bg=self.bg, fg=self.fg).pack(side="left")
        self.osc_port_var = tk.StringVar(value=str(self.config.get("osc_port", 9000)))
        self.osc_port_entry = tk.Entry(settings_row, textvariable=self.osc_port_var, width=6, bg=self.entry_bg, fg=self.entry_fg)
        self.osc_port_entry.pack(side="left", padx=(4, 10))

        tk.Label(settings_row, text="Cooldown:", bg=self.bg, fg=self.fg).pack(side="left")
        self.cooldown_var = tk.StringVar(value=str(self.config.get("cooldown_seconds", 5)))
        self.cooldown_entry = tk.Entry(settings_row, textvariable=self.cooldown_var, width=5, bg=self.entry_bg, fg=self.entry_fg)
        self.cooldown_entry.pack(side="left", padx=(4, 4))
        tk.Label(settings_row, text="seconds", bg=self.bg, fg=self.fg).pack(side="left")

        self.apply_settings_button = tk.Button(
            settings_row,
            text="Apply",
            command=self.apply_runtime_settings,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            width=10,
        )
        self.apply_settings_button.pack(side="left", padx=(10, 0))

        self.remote_frame = tk.LabelFrame(self.top, text="Phone Remote", bg=self.bg, fg=self.fg, padx=8, pady=6)
        self.remote_frame.pack(fill="x", pady=(6, 0))

        self.remote_status_var = tk.StringVar(value="Running" if self.remote_running else "Stopped")
        self.local_ip_var = tk.StringVar(value=self.get_local_ip())
        self.web_port_var = tk.StringVar(value=str(self.config.get("web_port", 8787)))
        self.remote_url_var = tk.StringVar(value=self.get_remote_url())

        tk.Label(self.remote_frame, text="Status:", bg=self.bg, fg=self.fg).pack(side="left")
        self.remote_status_label = tk.Label(self.remote_frame, textvariable=self.remote_status_var, bg=self.bg, fg=self.fg, width=9, anchor="w")
        self.remote_status_label.pack(side="left", padx=(4, 12))

        tk.Label(self.remote_frame, text="Local IP:", bg=self.bg, fg=self.fg).pack(side="left")
        self.local_ip_label = tk.Label(self.remote_frame, textvariable=self.local_ip_var, bg=self.bg, fg=self.fg, width=15, anchor="w")
        self.local_ip_label.pack(side="left", padx=(4, 12))

        tk.Label(self.remote_frame, text="Web port:", bg=self.bg, fg=self.fg).pack(side="left")
        self.web_port_entry = tk.Entry(self.remote_frame, textvariable=self.web_port_var, width=7, bg=self.entry_bg, fg=self.entry_fg)
        self.web_port_entry.pack(side="left", padx=(4, 12))

        tk.Label(self.remote_frame, text="URL:", bg=self.bg, fg=self.fg).pack(side="left")
        self.remote_url_label = tk.Label(self.remote_frame, textvariable=self.remote_url_var, bg=self.bg, fg=self.fg, anchor="w")
        self.remote_url_label.pack(side="left", fill="x", expand=True, padx=(4, 12))

        self.qr_button = tk.Button(
            self.remote_frame,
            text="QR Code",
            command=self.show_qr_window,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            width=10,
        )
        self.qr_button.pack(side="left", padx=(0, 6))

        self.start_remote_button = tk.Button(
            self.remote_frame,
            text="Start Remote",
            command=self.start_remote_server,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            width=13,
        )
        self.start_remote_button.pack(side="left", padx=(0, 6))

        self.copy_url_button = tk.Button(
            self.remote_frame,
            text="Copy URL",
            command=self.copy_remote_url,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            width=10,
        )
        self.copy_url_button.pack(side="left")

        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = tk.Label(self.top, textvariable=self.status_var, bg=self.bg, fg=self.fg)
        self.status_label.pack(anchor="w", pady=(4, 0))

        self.last_sent_var = tk.StringVar(value="Last sent: none")

        self.tabs_frame = tk.Frame(self.root, bg=self.bg)
        self.tabs_frame.pack(fill="x", padx=10, pady=(4, 4))

        self.tab_buttons = []
        self.load_buttons = []
        for i in range(5):
            holder = tk.Frame(self.tabs_frame, bg=self.bg)
            holder.pack(side="left", padx=(0, 8))

            tab_text = display_name_from_file(config_path_from_tab(self.settings["tabs"][i]))
            tab_btn = tk.Button(
                holder,
                text=tab_text,
                width=max(12, min(28, len(tab_text) + 2)),
                command=lambda idx=i: self.switch_tab(idx),
            )
            tab_btn.pack(side="left")

            load_btn = tk.Button(
                holder,
                text="Load",
                width=7,
                command=lambda idx=i: self.load_json_for_tab(idx),
            )
            load_btn.pack(side="left", padx=(2, 0))

            self.tab_buttons.append(tab_btn)
            self.load_buttons.append(load_btn)

        self.file_var = tk.StringVar()
        self.file_label = tk.Label(self.tabs_frame, textvariable=self.file_var, bg=self.bg, fg=self.fg)
        self.file_label.pack(side="left", padx=(10, 0))

        self.grid = tk.Frame(self.root, bg=self.bg)
        self.grid.pack(fill="both", expand=True, padx=10, pady=4)

        self.bottom = tk.Frame(self.root, bg=self.bg)
        self.bottom.pack(fill="x", padx=10, pady=(4, 10))

        self.custom_label = tk.Label(self.bottom, text="Custom message:", bg=self.bg, fg=self.fg)
        self.custom_label.pack(anchor="w")

        row = tk.Frame(self.bottom, bg=self.bg)
        row.pack(fill="x", pady=(4, 0))

        self.custom_text = tk.StringVar()
        self.custom_entry = tk.Entry(row, textvariable=self.custom_text, bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.entry_fg)
        self.custom_entry.pack(side="left", fill="x", expand=True, ipady=6)

        self.custom_button = tk.Button(
            row,
            text="Send Custom",
            width=16,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            command=self.send_custom,
        )
        self.custom_button.pack(side="left", padx=(8, 0))

        self.reload_button = tk.Button(
            row,
            text="Reload Current",
            width=14,
            bg=self.button_bg,
            fg=self.button_fg,
            activebackground=self.button_bg,
            activeforeground=self.button_fg,
            command=self.reload_current,
        )
        self.reload_button.pack(side="left", padx=(8, 0))

        self.update_header()
        self.update_tab_styles()

    def apply_runtime_settings(self):
        try:
            port = int(self.osc_port_var.get())
            cooldown = max(0, int(float(self.cooldown_var.get())))
        except ValueError:
            messagebox.showerror("Invalid settings", "Port and cooldown must be numbers.")
            return

        self.osc_ip = self.osc_ip_var.get().strip() or "127.0.0.1"
        self.osc_port = port
        self.cooldown_seconds = cooldown

        self.config["osc_ip"] = self.osc_ip
        self.config["osc_port"] = self.osc_port
        self.config["cooldown_seconds"] = self.cooldown_seconds
        try:
            save_json(self.current_config_path, self.config)
        except Exception:
            pass

        self.status_var.set(f"Settings applied. Cooldown: {self.cooldown_seconds}s")

    def populate_grid(self):
        for widget in self.grid.winfo_children():
            widget.destroy()
        self.buttons = []
        self.last_button = None

        phrases = self.config["phrases"]
        self.columns = int(self.config.get("columns", 8))

        for i, phrase in enumerate(phrases):
            label = self.make_button_label(phrase)
            is_clear = bool(phrase.get("is_clear", False))
            bg = self.clear_bg if is_clear else self.button_bg
            active = self.clear_active if is_clear else self.button_bg

            btn = tk.Button(
                self.grid,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg=bg,
                fg=self.button_fg,
                activebackground=active,
                activeforeground=self.button_fg,
                width=15,
                height=4,
                wraplength=135,
                relief="raised",
                command=lambda p=phrase: self.click_phrase(p),
            )
            r = i // self.columns
            c = i % self.columns
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            self.buttons.append((btn, phrase))

        for c in range(self.columns):
            self.grid.grid_columnconfigure(c, weight=1)
        for r in range(8):
            self.grid.grid_rowconfigure(r, weight=1)

    def update_header(self):
        self.osc_ip = str(self.config.get("osc_ip", "127.0.0.1"))
        self.osc_port = int(self.config.get("osc_port", 9000))
        self.cooldown_seconds = int(self.config.get("cooldown_seconds", 5))
        if hasattr(self, "osc_ip_var"):
            self.osc_ip_var.set(self.osc_ip)
            self.osc_port_var.set(str(self.osc_port))
            self.cooldown_var.set(str(self.cooldown_seconds))
        if hasattr(self, "web_port_var"):
            self.web_port = int(self.config.get("web_port", self.web_port))
            self.web_port_var.set(str(self.web_port))
            self.refresh_remote_labels()
        board_name = display_name_from_file(self.current_config_path)
        if hasattr(self, "board_title_var"):
            self.board_title_var.set(board_name)

        try:
            shown = self.current_config_path.relative_to(APP_DIR)
        except Exception:
            shown = self.current_config_path
        self.file_var.set(f"Current JSON: {shown}")

    def update_tab_styles(self):
        for i, btn in enumerate(self.tab_buttons):
            active = i == self.active_tab
            tab_text = display_name_from_file(config_path_from_tab(self.settings["tabs"][i]))
            btn.configure(
                text=tab_text,
                width=max(12, min(28, len(tab_text) + 2)),
                bg=self.tab_active if active else self.tab_bg,
                fg=self.button_fg,
                activebackground=self.tab_active if active else self.tab_bg,
                activeforeground=self.button_fg,
            )
            self.load_buttons[i].configure(
                bg=self.button_bg,
                fg=self.button_fg,
                activebackground=self.button_bg,
                activeforeground=self.button_fg,
            )

    def make_button_label(self, phrase):
        en = phrase.get("button_en", "").strip()
        ja = phrase.get("button_ja", "").strip()
        if en and ja:
            return f"{en}\n{ja}"
        return en or ja or "Empty"

    def click_phrase(self, phrase):
        self.apply_runtime_settings_silent()
        text = phrase.get("message", "")
        is_clear = bool(phrase.get("is_clear", False))
        try:
            self.send_chatbox(text, True)
            self.mark_last_button(phrase)
            shown = "[cleared text box]" if is_clear else text
            self.last_sent_var.set(f"Last sent: {shown}")
            if hasattr(self, "board_phrase_var"):
                self.board_phrase_var.set(f"Last sent: {shown}")
            self.start_cooldown()
        except Exception as e:
            messagebox.showerror("OSC send failed", f"Could not send OSC message:\n\n{e}")

    def apply_runtime_settings_silent(self):
        try:
            self.osc_ip = self.osc_ip_var.get().strip() or "127.0.0.1"
            self.osc_port = int(self.osc_port_var.get())
            self.cooldown_seconds = max(0, int(float(self.cooldown_var.get())))
        except Exception:
            pass

    def send_custom(self):
        self.apply_runtime_settings_silent()
        text = self.custom_text.get().strip()
        if not text:
            messagebox.showinfo("No message", "Type a custom message first.")
            return
        try:
            self.send_chatbox(text, True)
            self.mark_last_button(None)
            self.last_sent_var.set(f"Last sent: {text}")
            if hasattr(self, "board_phrase_var"):
                self.board_phrase_var.set(f"Last sent: {text}")
            self.start_cooldown()
        except Exception as e:
            messagebox.showerror("OSC send failed", f"Could not send OSC message:\n\n{e}")

    def mark_last_button(self, phrase):
        self.last_button = None
        for btn, p in self.buttons:
            is_clear = bool(p.get("is_clear", False))
            btn.configure(bg=self.clear_bg if is_clear else self.button_bg)
            if phrase is not None and p is phrase:
                self.last_button = btn
                btn.configure(bg=self.last_bg)

    def start_cooldown(self):
        self.cooldown_remaining = self.cooldown_seconds
        self.set_locked(True)
        self.tick()

    def tick(self):
        if self.cooldown_remaining <= 0:
            self.set_locked(False)
            self.status_var.set("Ready.")
            return
        self.status_var.set(f"Cooldown: {self.cooldown_remaining}s")
        self.cooldown_remaining -= 1
        self.root.after(1000, self.tick)

    def set_locked(self, locked):
        state = "disabled" if locked else "normal"
        for btn, phrase in self.buttons:
            btn.configure(state=state)
            if locked:
                if btn == self.last_button:
                    btn.configure(bg=self.last_bg, disabledforeground="#ffffff")
                else:
                    btn.configure(bg=self.disabled_bg, disabledforeground="#d0d0d0")
            else:
                if btn == self.last_button:
                    btn.configure(bg=self.last_bg)
                else:
                    btn.configure(bg=self.clear_bg if phrase.get("is_clear", False) else self.button_bg)

        for widget in [
            self.custom_button, self.custom_entry, self.reload_button,
            self.dark_button, self.osc_ip_entry, self.osc_port_entry,
            self.cooldown_entry, self.apply_settings_button
        ]:
            widget.configure(state=state)

        if hasattr(self, "web_port_entry"):
            self.web_port_entry.configure(state=state)

        for b in self.tab_buttons + self.load_buttons:
            b.configure(state=state)

    def switch_tab(self, idx):
        self.active_tab = idx
        self.settings["active_tab"] = idx
        self.current_config_path = config_path_from_tab(self.settings["tabs"][idx])
        try:
            self.config = self.load_current_config()
        except Exception as e:
            messagebox.showerror("JSON load failed", f"Could not load this board JSON:\n\n{self.current_config_path}\n\n{e}")
            self.config = normalise_config(DEFAULT_CONFIG.copy())
        self.last_sent_var.set("Last sent: none")
        if hasattr(self, "board_phrase_var"):
            self.board_phrase_var.set("Last sent: none")
        self.update_header()
        self.update_tab_styles()
        self.populate_grid()
        self.save_settings()

    def load_json_for_tab(self, idx):
        path = filedialog.askopenfilename(
            title=f"Load JSON for Board {idx+1}",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        path = Path(path)
        try:
            cfg = normalise_config(load_json(path))
        except Exception as e:
            messagebox.showerror("Invalid JSON", f"Could not load JSON:\n\n{e}")
            return

        try:
            stored_path = str(path.relative_to(APP_DIR))
        except Exception:
            stored_path = str(path)

        self.settings["tabs"][idx]["file"] = stored_path
        self.active_tab = idx
        self.settings["active_tab"] = idx
        self.current_config_path = path
        self.config = cfg
        self.save_settings()
        self.update_header()
        self.update_tab_styles()
        self.populate_grid()

    def reload_current(self):
        self.switch_tab(self.active_tab)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.save_settings()
        self.rebuild_window()

    def rebuild_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.set_theme_values()
        self.root.configure(bg=self.bg)
        self.buttons = []
        self.build_ui()
        self.populate_grid()

if __name__ == "__main__":
    root = tk.Tk()
    PhraseBoardApp(root)
    root.mainloop()

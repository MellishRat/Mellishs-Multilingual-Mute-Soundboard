import json
import socket
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = APP_DIR / "board_settings.json"

DEFAULT_CONFIG = {
    "osc_ip": "127.0.0.1",
    "osc_port": 9000,
    "cooldown_seconds": 5,
    "dark_mode": True,
    "columns": 8,
    "window_width": 1280,
    "window_height": 820,
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
    if not p.is_absolute():
        p = APP_DIR / p
    return p

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

        self.settings["tabs"][idx]["file"] = str(path)
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

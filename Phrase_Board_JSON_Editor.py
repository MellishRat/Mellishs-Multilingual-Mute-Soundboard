import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "host.json"

def load_config(path):
    with Path(path).open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    phrases = cfg.setdefault("phrases", [])
    while len(phrases) < 64:
        phrases.append({"button_en": f"Empty {len(phrases)+1}", "button_ja": "空", "message": ""})
    cfg["phrases"] = phrases[:64]
    cfg.setdefault("osc_ip", "127.0.0.1")
    cfg.setdefault("osc_port", 9000)
    cfg.setdefault("cooldown_seconds", 5)
    cfg.setdefault("dark_mode", True)
    cfg.setdefault("columns", 8)
    cfg.setdefault("window_width", 1280)
    cfg.setdefault("window_height", 820)
    return cfg

def save_config(path, cfg):
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

class PhraseEditor:
    def __init__(self, root):
        self.root = root
        self.current_path = CONFIG_PATH
        self.cfg = load_config(self.current_path)
        self.phrases = self.cfg["phrases"]
        self.selected_index = 0
        self.buttons = []

        self.bg = "#151515"
        self.panel = "#202020"
        self.fg = "#ffffff"
        self.button_bg = "#303030"
        self.selected_bg = "#247a3d"
        self.clear_bg = "#8b3030"

        self.build_ui()
        self.select_slot(0)

    def build_ui(self):
        self.root.title("Mellish Phrase JSON Editor v0.4")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 680)
        self.root.configure(bg=self.bg)

        top = tk.Frame(self.root, bg=self.bg)
        top.pack(fill="x", padx=10, pady=10)

        title_row = tk.Frame(top, bg=self.bg)
        title_row.pack(fill="x")
        tk.Label(title_row, text="Phrase JSON Editor", font=("Segoe UI", 17, "bold"), bg=self.bg, fg=self.fg).pack(side="left", anchor="w")
        tk.Button(title_row, text="Open JSON", command=self.open_json, bg=self.button_bg, fg=self.fg).pack(side="right")

        self.path_var = tk.StringVar()
        tk.Label(top, textvariable=self.path_var, bg=self.bg, fg=self.fg).pack(anchor="w")
        tk.Label(top, text="Click a slot, edit the English button label, Japanese button label, and the message sent to VRChat.", bg=self.bg, fg=self.fg).pack(anchor="w")

        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        self.grid = tk.Frame(main, bg=self.bg)
        self.grid.pack(side="left", fill="both", expand=True)

        self.build_grid()

        editor = tk.Frame(main, bg=self.panel, padx=12, pady=12)
        editor.pack(side="right", fill="y", padx=(10, 0))

        self.slot_var = tk.StringVar()
        tk.Label(editor, textvariable=self.slot_var, font=("Segoe UI", 13, "bold"), bg=self.panel, fg=self.fg).pack(anchor="w", pady=(0, 10))

        tk.Label(editor, text="Button English:", bg=self.panel, fg=self.fg).pack(anchor="w")
        self.en_var = tk.StringVar()
        tk.Entry(editor, textvariable=self.en_var, width=38).pack(fill="x", pady=(2, 8))

        tk.Label(editor, text="Button Japanese:", bg=self.panel, fg=self.fg).pack(anchor="w")
        self.ja_var = tk.StringVar()
        tk.Entry(editor, textvariable=self.ja_var, width=38).pack(fill="x", pady=(2, 8))

        tk.Label(editor, text="Message sent to VRChat:", bg=self.panel, fg=self.fg).pack(anchor="w")
        self.msg_text = tk.Text(editor, width=46, height=12, wrap="word")
        self.msg_text.pack(fill="x", pady=(2, 8))

        self.clear_var = tk.BooleanVar()
        tk.Checkbutton(
            editor,
            text="This is the Clear Text Box button",
            variable=self.clear_var,
            bg=self.panel,
            fg=self.fg,
            selectcolor=self.panel,
            activebackground=self.panel,
            activeforeground=self.fg,
        ).pack(anchor="w", pady=(2, 10))

        tk.Button(editor, text="Apply To Selected Slot", command=self.apply_selected, bg="#247a3d", fg="#ffffff").pack(fill="x", pady=(4, 6))
        tk.Button(editor, text="Save JSON", command=self.save, bg="#305c8b", fg="#ffffff").pack(fill="x", pady=6)
        tk.Button(editor, text="Save As New JSON", command=self.save_as, bg="#305c8b", fg="#ffffff").pack(fill="x", pady=6)
        tk.Button(editor, text="Reload JSON", command=self.reload, bg=self.button_bg, fg=self.fg).pack(fill="x", pady=6)

        ttk.Separator(editor, orient="horizontal").pack(fill="x", pady=12)

        tk.Label(
            editor,
            text="OSC target and cooldown are edited in the main board app.",
            wraplength=320,
            justify="left",
            bg=self.panel,
            fg=self.fg,
        ).pack(anchor="w")

        self.update_path_label()

    def build_grid(self):
        for w in self.grid.winfo_children():
            w.destroy()
        self.buttons = []
        for i, phrase in enumerate(self.phrases):
            btn = tk.Button(
                self.grid,
                text=self.make_label(phrase),
                font=("Segoe UI", 9, "bold"),
                bg=self.clear_bg if phrase.get("is_clear", False) else self.button_bg,
                fg=self.fg,
                width=15,
                height=4,
                wraplength=130,
                command=lambda idx=i: self.select_slot(idx)
            )
            r = i // 8
            c = i % 8
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            self.buttons.append(btn)

        for c in range(8):
            self.grid.grid_columnconfigure(c, weight=1)
        for r in range(8):
            self.grid.grid_rowconfigure(r, weight=1)

    def update_path_label(self):
        try:
            shown = self.current_path.relative_to(APP_DIR)
        except Exception:
            shown = self.current_path
        self.path_var.set(f"Editing: {shown}")

    def make_label(self, phrase):
        en = phrase.get("button_en", "").strip()
        ja = phrase.get("button_ja", "").strip()
        return f"{en}\n{ja}" if en and ja else (en or ja or "Empty")

    def refresh_buttons(self):
        for i, phrase in enumerate(self.phrases):
            bg = self.selected_bg if i == self.selected_index else (self.clear_bg if phrase.get("is_clear", False) else self.button_bg)
            self.buttons[i].configure(text=self.make_label(phrase), bg=bg)

    def select_slot(self, idx):
        self.selected_index = idx
        phrase = self.phrases[idx]
        self.slot_var.set(f"Slot {idx + 1} of 64")
        self.en_var.set(phrase.get("button_en", ""))
        self.ja_var.set(phrase.get("button_ja", ""))
        self.msg_text.delete("1.0", "end")
        self.msg_text.insert("1.0", phrase.get("message", ""))
        self.clear_var.set(bool(phrase.get("is_clear", False)))
        self.refresh_buttons()

    def apply_selected(self):
        p = self.phrases[self.selected_index]
        p["button_en"] = self.en_var.get()
        p["button_ja"] = self.ja_var.get()
        p["message"] = self.msg_text.get("1.0", "end").rstrip("\n")
        p["is_clear"] = bool(self.clear_var.get())
        self.refresh_buttons()

    def save(self):
        self.apply_selected()
        save_config(self.current_path, self.cfg)
        messagebox.showinfo("Saved", "JSON saved.")

    def save_as(self):
        self.apply_selected()
        path = filedialog.asksaveasfilename(
            title="Save phrase board JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        self.current_path = Path(path)
        save_config(self.current_path, self.cfg)
        self.update_path_label()
        messagebox.showinfo("Saved", "JSON saved.")

    def reload(self):
        self.cfg = load_config(self.current_path)
        self.phrases = self.cfg["phrases"]
        self.build_grid()
        self.select_slot(0)
        self.update_path_label()

    def open_json(self):
        path = filedialog.askopenfilename(
            title="Open phrase board JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.current_path = Path(path)
            self.cfg = load_config(self.current_path)
            self.phrases = self.cfg["phrases"]
        except Exception as e:
            messagebox.showerror("Open failed", f"Could not open JSON:\n\n{e}")
            return
        self.build_grid()
        self.select_slot(0)
        self.update_path_label()

if __name__ == "__main__":
    root = tk.Tk()
    PhraseEditor(root)
    root.mainloop()

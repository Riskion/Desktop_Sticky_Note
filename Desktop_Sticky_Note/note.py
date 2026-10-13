
import json
import tkinter as tk
import ctypes
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def hide_taskbar_icon(window):
    """Hide this window's icon from the Windows taskbar."""
    try:
        window.update_idletasks()
        hwnd = window.winfo_id()

        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        user32 = ctypes.windll.user32

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW

        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020

        user32.SetWindowPos(
            hwnd,
            None,
            0, 0, 0, 0,
            SWP_NOSIZE | SWP_NOMOVE |
            SWP_NOZORDER | SWP_FRAMECHANGED
        )
    except (AttributeError, OSError):
        pass


APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "note_data.json"
WOLF_FILE = APP_DIR / "wolf.png"

NOTE_W, NOTE_H = 320, 460
ICON_SIZE = 96

BG = "#202124"
PANEL = "#292a2d"
TEXT = "#e8eaed"
MUTED = "#9aa0a6"
ACCENT = "#8ab4f8"
BORDER = "#3c4043"

# Windows uses this colour as the transparent window background.
TRANSPARENT_KEY = "#ff00ff"

data = {}
wolf = None
wolf_image = None
_save_job = None
transparent_supported = False


def load_data():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


data = load_data()


root = tk.Tk()
root.title("Desktop Sticky Note")
root.configure(bg=BG)
root.minsize(260, 330)
root.geometry(data.get("geometry", f"{NOTE_W}x{NOTE_H}+80+80"))
root.attributes("-topmost", bool(data.get("always_on_top", True)))

# Hide the main window from the Windows taskbar.
root.withdraw()

def show_note_without_taskbar():
    import ctypes

    root.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())

    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_APPWINDOW = 0x00040000

    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
    )

    root.deiconify()
    root.update_idletasks()

root.after(100, show_note_without_taskbar)


top_var = tk.BooleanVar(value=bool(data.get("always_on_top", True)))
status_var = tk.StringVar(value="Auto-saves as you type")



def save_data():
    global _save_job

    try:
        if wolf is not None and wolf.winfo_exists():
            wolf_position = f"+{wolf.winfo_x()}+{wolf.winfo_y()}"
        else:
            wolf_position = data.get("wolf_position", "+80+80")

        DATA_FILE.write_text(
            json.dumps({
                "text": editor.get("1.0", "end-1c"),
                "geometry": root.geometry(),
                "always_on_top": top_var.get(),
                "wolf_position": wolf_position,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        status_var.set("Saved")

    except (OSError, tk.TclError):
        pass


# ---------- Header ----------

header = tk.Frame(root, bg=PANEL, padx=8, pady=7)
header.pack(fill="x")

title_label = tk.Label(
    header,
    text="✎  QUICK NOTE",
    bg=PANEL,
    fg=ACCENT,
    font=("Segoe UI", 10, "bold")
)
title_label.pack(side="left")


def set_topmost():
    enabled = bool(top_var.get())

    root.attributes("-topmost", enabled)

    if enabled:
        root.lift()
    else:
        # Allow other windows, such as games, to appear above the note.
        root.attributes("-topmost", False)
        root.lower()

    save_data()


# ---------- On top button ----------

pin_button = tk.Checkbutton(
    header,
    text="On top",
    variable=top_var,
    command=set_topmost,
    bg=PANEL,
    fg=TEXT,
    selectcolor=BG,
    activebackground=PANEL,
    activeforeground=TEXT,
    font=("Segoe UI", 9),
    bd=0
)
pin_button.pack(side="right", padx=(4, 0))


# ---------- SPEAK BUTTON ----------

speak_active = False






def start_dictation():
    global speak_active

    # Clicking while ON switches the button back OFF.
    # Windows Voice Typing itself must be stopped separately with Win+H.
    if speak_active:
        speak_active = False
        speak_button.config(
            text="🎙 OFF",
            bg="#C62828",
            activebackground="#C62828",
            fg="white",
            activeforeground="white"
        )
        return

    speak_active = True

    speak_button.config(
        text="🎙 ON",
        bg="#16803C",
        activebackground="#16803C",
        fg="white",
        activeforeground="white"
    )

    root.deiconify()
    root.lift()
    root.attributes("-topmost", top_var.get())
    editor.focus_set()

    def open_voice_typing():
        try:
            import time

            user32 = ctypes.windll.user32
            VK_LWIN = 0x5B
            VK_H = 0x48
            KEYEVENTF_KEYUP = 0x0002

            user32.keybd_event(VK_LWIN, 0, 0, 0)
            time.sleep(0.1)
            user32.keybd_event(VK_H, 0, 0, 0)
            time.sleep(0.1)
            user32.keybd_event(VK_H, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

        except Exception as error:
            print("Voice Typing error:", error)

    root.after(800, open_voice_typing)




speak_button = tk.Button(
    header,
    text="🎙 OFF",
    command=start_dictation,
    bg="#C62828",
    fg="white",
    activebackground="#C62828",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 8),
    cursor="hand2",
    padx=2,
    pady=0
)
speak_button.pack(side="right", padx=(2, 0))

# ---------- Collapse button ----------


fold_button = tk.Button(
    header,
    text="🐺",
    command=lambda: collapse_note(),
    bg=PANEL,
    fg=TEXT,
    activebackground=BORDER,
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    font=("Segoe UI Emoji", 12),
    cursor="hand2",
    padx=5
)
fold_button.pack(side="right")


# ---------- Note editor ----------

body = tk.Frame(root, bg=BG, padx=10, pady=10)
body.pack(fill="both", expand=True)

editor = tk.Text(
    body,
    wrap="word",
    undo=True,
    bg=BG,
    fg=TEXT,
    insertbackground=TEXT,
    selectbackground="#3c5a7a",
    relief="flat",
    bd=0,
    font=("Segoe UI", 11),
    padx=3,
    pady=3,
    spacing1=2,
    spacing3=4,
    highlightthickness=1,
    highlightbackground=BORDER,
    highlightcolor=ACCENT
)
editor.pack(fill="both", expand=True)
editor.insert("1.0", data.get("text", ""))


# ---------- Footer ----------

footer = tk.Frame(root, bg=PANEL, padx=10, pady=7)
footer.pack(fill="x")

tk.Label(
    footer,
    textvariable=status_var,
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 8)
).pack(side="left")


def clear_note():
    if editor.get("1.0", "end-1c").strip():
        editor.delete("1.0", "end")
        save_data()


clear_btn = tk.Button(
    footer,
    text="Clear",
    command=clear_note,
    bg=BORDER,
    fg=TEXT,
    activebackground="#5f6368",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    padx=10,
    pady=4,
    font=("Segoe UI", 9)
)
clear_btn.pack(side="right")


# ---------- Floating wolf icon ----------


def load_wolf_image():
    """Load wolf.png with clean transparency for Windows."""
    if not WOLF_FILE.is_file():
        return None

    try:
        if PIL_AVAILABLE:
            image = Image.open(WOLF_FILE).convert("RGBA")
            image = image.resize(
                (ICON_SIZE, ICON_SIZE),
                Image.Resampling.LANCZOS
            )

            # Convert transparent pixels to Windows' transparent colour.
            pixels = image.load()
            for y in range(image.height):
                for x in range(image.width):
                    r, g, b, a = pixels[x, y]
                    if a < 128:
                        pixels[x, y] = (255, 0, 255, 255)
                    else:
                        pixels[x, y] = (r, g, b, 255)

            return ImageTk.PhotoImage(image)

        image = tk.PhotoImage(file=str(WOLF_FILE))
        if image.width() != ICON_SIZE or image.height() != ICON_SIZE:
            factor = max(
                1,
                image.width() // ICON_SIZE,
                image.height() // ICON_SIZE
            )
            image = image.subsample(factor, factor)

        return image

    except (tk.TclError, OSError, ValueError) as error:
        print(f"Could not load wolf.png: {error}")
        return None




def collapse_note():
    global wolf, wolf_image, transparent_supported

    if wolf is not None and wolf.winfo_exists():
        return

    save_data()

    # Use the previously saved wolf position.
    position = data.get("wolf_position", "+80+80")

    try:
        if position.startswith("+"):
            parts = position[1:].split("+")
            x, y = int(parts[0]), int(parts[1])
        else:
            x, y = root.winfo_x(), root.winfo_y()
    except (ValueError, IndexError):
        x, y = root.winfo_x(), root.winfo_y()

    root.withdraw()

    wolf = tk.Toplevel(root)
    wolf.overrideredirect(True)
    wolf.geometry(f"{ICON_SIZE}x{ICON_SIZE}+{x}+{y}")
    wolf.attributes("-topmost", True)

    # On Windows, the chosen colour becomes transparent.
    try:
        wolf.configure(bg=TRANSPARENT_KEY)
        wolf.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        transparent_supported = True
    except tk.TclError:
        transparent_supported = False
        wolf.configure(bg=BG)

    wolf_image = load_wolf_image()

    if wolf_image is not None:
        wolf_label = tk.Label(
            wolf,
            image=wolf_image,
            bg=TRANSPARENT_KEY if transparent_supported else BG,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
    else:
        # Temporary fallback until wolf.png is added.
        message = "🐺" if not WOLF_FILE.exists() else "!"
        wolf_label = tk.Label(
            wolf,
            text=message,
            bg=TRANSPARENT_KEY if transparent_supported else PANEL,
            fg=ACCENT,
            font=("Segoe UI Emoji", 30),
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )

    wolf_label.pack(fill="both", expand=True)

    
    drag = {
        "x": 0,
        "y": 0,
        "start_x": 0,
        "start_y": 0,
        "moved": False
    }

    def start_drag(event):
        drag["x"] = event.x_root - wolf.winfo_x()
        drag["y"] = event.y_root - wolf.winfo_y()
        drag["start_x"] = event.x_root
        drag["start_y"] = event.y_root
        drag["moved"] = False

    def move_drag(event):
        dx = event.x_root - drag["start_x"]
        dy = event.y_root - drag["start_y"]

        if abs(dx) > 4 or abs(dy) > 4:
            drag["moved"] = True

        if drag["moved"]:
            new_x = event.x_root - drag["x"]
            new_y = event.y_root - drag["y"]
            wolf.geometry(
                f"{ICON_SIZE}x{ICON_SIZE}+{new_x}+{new_y}"
            )

    def finish_drag(event):
        if drag["moved"]:
            save_data()
        else:
            restore_note()

    for widget in (wolf, wolf_label):
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", move_drag)
        widget.bind("<ButtonRelease-1>", finish_drag)



def restore_note():
    global wolf, wolf_image

    if wolf is not None:
        try:
            wolf.destroy()
        except tk.TclError:
            pass

    wolf = None
    wolf_image = None

    root.deiconify()
    root.lift()
    root.attributes("-topmost", top_var.get())
    editor.focus_set()
    save_data()


# ---------- Automatic saving ----------



def schedule_save(event=None):
    global _save_job

    if _save_job is not None:
        try:
            root.after_cancel(_save_job)
        except tk.TclError:
            pass

    status_var.set("Typing…")
    _save_job = root.after(800, save_data)


editor.bind("<KeyRelease>", schedule_save)
editor.bind("<<Paste>>", schedule_save)
editor.bind("<<Cut>>", schedule_save)



def stop_dictation_indicator():
    global speak_active

    speak_active = False

    speak_button.config(
        text="🎙 OFF",
        bg="#C62828",
        activebackground="#C62828",
        fg="white",
        activeforeground="white"
    )


def handle_note_click(event):
    # Keep the button green when starting dictation.
    if event.widget == speak_button:
        return

    # Any other click inside Quick Note turns the button red.
    stop_dictation_indicator()
root.update_idletasks()


root.bind_all("<Button-1>", handle_note_click, add="+")


editor.bind("<KeyRelease>", schedule_save)
editor.bind("<<Paste>>", schedule_save)
editor.bind("<<Cut>>", schedule_save)

editor.bind("<FocusOut>", lambda event: print("EDITOR LOST FOCUS", flush=True))
editor.bind("<FocusIn>", lambda event: print("EDITOR GOT FOCUS", flush=True))


def on_configure(event):
    if event.widget is root and root.state() == "normal":
        schedule_save()


root.bind("<Configure>", on_configure)


def periodic_save():
    save_data()
    root.after(10000, periodic_save)


def close_app():
    save_data()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)

# Temporarily disabled while testing dictation.
# root.after(10000, periodic_save)

editor.focus_set()

root.mainloop()
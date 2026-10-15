
import ctypes
import json
import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ============================================================
# FILES AND SETTINGS
# ============================================================

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "note_data.json"
WOLF_FILE = APP_DIR / "wolf.png"
OPEN_SOUND = APP_DIR / "Cara-Delevingne-Voice-open.mp3"
CLOSE_SOUND = APP_DIR / "Cara-Delevingne-Voice-closed.mp3"

NOTE_W, NOTE_H = 320, 460
ICON_SIZE = 96

BG = "#202124"
PANEL = "#292a2d"
TEXT = "#e8eaed"
MUTED = "#9aa0a6"
ACCENT = "#8ab4f8"
BORDER = "#3c4043"
TRANSPARENT_KEY = "#ff00ff"

data = {}
wolf = None
wolf_image = None
fold_button_image = None
_save_job = None
speak_active = False
transparent_supported = False


def load_data():
    try:
        loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


data = load_data()
sound_muted = bool(data.get("sound_muted", False))


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.withdraw()
root.title("Desktop Sticky Note")
root.configure(bg=BG)
root.minsize(260, 330)
root.geometry(data.get("geometry", f"{NOTE_W}x{NOTE_H}+80+80"))

top_var = tk.BooleanVar(
    value=bool(data.get("always_on_top", True))
)
root.attributes("-topmost", top_var.get())

status_var = tk.StringVar(value="Auto-saves as you type")


def show_note_without_taskbar():
    """Try to keep the main note off the Windows taskbar."""
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())

        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW,
        )
        root.update_idletasks()

    except (AttributeError, OSError, tk.TclError) as error:
        print(f"Could not hide taskbar icon: {error}")


root.after(100, show_note_without_taskbar)


# ============================================================
# SOUND
# ============================================================

def play_sound(sound_file):
    if sound_muted or not sound_file.is_file():
        return

    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(str(sound_file))
        pygame.mixer.music.play()

    except Exception as error:
        print(f"Could not play sound: {error}")


# ============================================================
# SAVE DATA
# ============================================================

def save_data():
    global _save_job

    _save_job = None

    try:
        if root.winfo_exists():
            data["geometry"] = root.geometry()
            data["always_on_top"] = bool(top_var.get())

        if editor.winfo_exists():
            data["text"] = editor.get("1.0", "end-1c")

        data["sound_muted"] = sound_muted

        if wolf is not None:
            try:
                if wolf.winfo_exists():
                    data["wolf_position"] = (
                        f"{wolf.winfo_x():+d}{wolf.winfo_y():+d}"
                    )
            except tk.TclError:
                pass

        temporary_file = DATA_FILE.with_suffix(".tmp")
        temporary_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_file.replace(DATA_FILE)

        status_var.set("Saved")

    except (OSError, tk.TclError, NameError) as error:
        print(f"Could not save note: {error}")


def schedule_save(event=None):
    global _save_job

    if _save_job is not None:
        try:
            root.after_cancel(_save_job)
        except tk.TclError:
            pass

    try:
        status_var.set("Typing…")
        _save_job = root.after(800, save_data)
    except tk.TclError:
        _save_job = None


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(root, bg=PANEL, padx=8, pady=7)
header.pack(fill="x")

title_label = tk.Label(
    header,
    text="",
    bg=PANEL,
    fg=ACCENT,
    font=("Segoe UI", 10, "bold"),
)
title_label.pack(side="left")


def set_topmost():
    enabled = bool(top_var.get())
    root.attributes("-topmost", enabled)

    if enabled:
        root.lift()
    else:
        root.attributes("-topmost", False)
        root.lower()

    save_data()


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
    bd=0,
)
pin_button.pack(side="right", padx=(4, 0))


# ============================================================
# SPEECH BUTTON / WINDOWS VOICE TYPING
# ============================================================

def set_speech_button(active):
    global speak_active

    speak_active = active

    if active:
        speak_button.config(
            text="🎙 ON",
            bg="#16803C",
            activebackground="#16803C",
            fg="white",
            activeforeground="white",
        )
    else:
        speak_button.config(
            text="SPEECH: OFF",
            bg="#C62828",
            activebackground="#C62828",
            fg="white",
            activeforeground="white",
        )


def open_voice_typing():
    """Send Win+H to Windows to open Voice Typing."""
    try:
        user32 = ctypes.windll.user32

        VK_LWIN = 0x5B
        VK_H = 0x48
        KEYEVENTF_KEYUP = 0x0002

        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_H, 0, 0, 0)
        user32.keybd_event(VK_H, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

    except Exception as error:
        print(f"Voice Typing error: {error}")


def start_dictation():
    if speak_active:
        set_speech_button(False)
        return

    set_speech_button(True)

    root.deiconify()
    root.lift()
    root.attributes("-topmost", bool(top_var.get()))

    root.update_idletasks()
    editor.focus_force()
    editor.mark_set("insert", "end-1c")
    editor.see("insert")

    # Allow Windows to focus the editor before sending Win+H.
    root.after(800, open_voice_typing)


speak_button = tk.Button(
    header,
    text="SPEECH: OFF",
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
    pady=0,
)
speak_button.pack(side="right", padx=(2, 0))


# ============================================================
# MUTE BUTTON
# ============================================================

def toggle_sound():
    global sound_muted

    sound_muted = not sound_muted
    update_sound_button()
    save_data()


def update_sound_button():
    if sound_muted:
        sound_button.config(
            text="SOUND: MUTED",
            bg="#C62828",
            activebackground="#A51F1F",
        )
    else:
        sound_button.config(
            text="SOUND: ON",
            bg="#16803C",
            activebackground="#11652F",
        )


sound_button = tk.Button(
    header,
    text="",
    command=toggle_sound,
    bg="#16803C",
    fg="white",
    activebackground="#11652F",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 7, "bold"),
    cursor="hand2",
    padx=8,
    pady=2,
)
sound_button.pack(side="right", padx=(2, 0))
update_sound_button()


# ============================================================
# NOTE EDITOR
# ============================================================

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
    highlightcolor=ACCENT,
)
editor.pack(fill="both", expand=True)
editor.insert("1.0", str(data.get("text", "")))
editor.edit_modified(False)


# ============================================================
# FOOTER
# ============================================================

footer = tk.Frame(root, bg=PANEL, padx=10, pady=7)
footer.pack(fill="x")

tk.Label(
    footer,
    textvariable=status_var,
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 8),
).pack(side="left")


def clear_note():
    if editor.get("1.0", "end-1c").strip():
        editor.delete("1.0", "end")
        editor.focus_set()
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
    font=("Segoe UI", 9),
)
clear_btn.pack(side="right")


# ============================================================
# WOLF IMAGE AND FLOATING ICON
# ============================================================

def load_wolf_image():
    """Load the original wolf.png for the compact floating icon."""
    if not WOLF_FILE.is_file():
        print(f"wolf.png was not found at: {WOLF_FILE}")
        return None

    try:
        if PIL_AVAILABLE:
            image = Image.open(WOLF_FILE).convert("RGBA")
            image = image.resize(
                (ICON_SIZE, ICON_SIZE),
                Image.Resampling.LANCZOS,
            )

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
                image.height() // ICON_SIZE,
            )
            image = image.subsample(factor, factor)

        return image

    except (tk.TclError, OSError, ValueError) as error:
        print(f"Could not load wolf.png: {error}")
        return None


def parse_position(position):
    """Read saved Tk positions, including negative screen coordinates."""
    import re

    match = re.search(r"([+-]\d+)([+-]\d+)$", str(position))

    if match:
        return int(match.group(1)), int(match.group(2))

    return 80, 80


def collapse_note():
    global wolf, wolf_image, transparent_supported

    if wolf is not None:
        try:
            if wolf.winfo_exists():
                return
        except tk.TclError:
            pass

    save_data()

    if not getattr(root, "_starting_compact", False):
        play_sound(CLOSE_SOUND)

    x, y = parse_position(data.get("wolf_position", "+80+80"))
    root.withdraw()

    wolf = tk.Toplevel(root)
    wolf.overrideredirect(True)
    wolf.geometry(f"{ICON_SIZE}x{ICON_SIZE}{x:+d}{y:+d}")
    wolf.attributes("-topmost", True)

    try:
        wolf.configure(bg=TRANSPARENT_KEY)
        wolf.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        transparent_supported = True
    except tk.TclError:
        transparent_supported = False
        wolf.configure(bg=BG)

    wolf_image = load_wolf_image()
    icon_bg = TRANSPARENT_KEY if transparent_supported else BG

    if wolf_image is not None:
        wolf_label = tk.Label(
            wolf,
            image=wolf_image,
            bg=icon_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
    else:
        wolf_label = tk.Label(
            wolf,
            text="🐺",
            bg=icon_bg,
            fg=ACCENT,
            font=("Segoe UI Emoji", 30),
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )

    wolf_label.pack(fill="both", expand=True)

    drag = {
        "offset_x": 0,
        "offset_y": 0,
        "start_x": 0,
        "start_y": 0,
        "moved": False,
    }

    def start_drag(event):
        drag["offset_x"] = event.x_root - wolf.winfo_x()
        drag["offset_y"] = event.y_root - wolf.winfo_y()
        drag["start_x"] = event.x_root
        drag["start_y"] = event.y_root
        drag["moved"] = False

    def move_drag(event):
        dx = event.x_root - drag["start_x"]
        dy = event.y_root - drag["start_y"]

        if abs(dx) > 4 or abs(dy) > 4:
            drag["moved"] = True

        if drag["moved"]:
            new_x = event.x_root - drag["offset_x"]
            new_y = event.y_root - drag["offset_y"]
            wolf.geometry(
                f"{ICON_SIZE}x{ICON_SIZE}{new_x:+d}{new_y:+d}"
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

    play_sound(OPEN_SOUND)

    root.withdraw()
    root.after(10, root.deiconify)
    root.after(30, root.lift)
    root.after(50, lambda: root.attributes("-topmost", bool(top_var.get())))
    root.after(100, editor.focus_set)
    root.after(150, save_data)


# Preserve the wolf image on the header's fold button.
try:
    fold_button_image = tk.PhotoImage(file=str(WOLF_FILE))
except (tk.TclError, OSError) as error:
    print(f"Could not load wolf.png for the fold button: {error}")
    fold_button_image = None


fold_button = tk.Button(
    header,
    image=fold_button_image,
    text="" if fold_button_image is not None else "🐺",
    command=collapse_note,
    bg=PANEL,
    fg=TEXT,
    activebackground=BORDER,
    relief="flat",
    bd=0,
    cursor="hand2",
    padx=5,
)
fold_button.pack(side="right")


# ============================================================
# EDITOR EVENTS AND AUTOSAVE
# ============================================================

def redraw_editor():
    """Request an idle redraw after text changes."""
    try:
        if editor.winfo_exists():
            editor.update_idletasks()
            editor.see("insert")
    except tk.TclError:
        pass


def on_editor_modified(event=None):
    if editor.edit_modified():
        editor.edit_modified(False)
        schedule_save()

        # One redraw request after an edit; no recurring refresh loop.
        root.after_idle(redraw_editor)


editor.bind("<<Modified>>", on_editor_modified)


def stop_dictation_indicator():
    set_speech_button(False)


def handle_note_click(event):
    if event.widget == speak_button:
        return

    stop_dictation_indicator()


root.bind_all("<Button-1>", handle_note_click, add="+")


def on_configure(event):
    if event.widget == root and root.state() == "normal":
        schedule_save()


root.bind("<Configure>", on_configure)


# ============================================================
# STARTUP AND SHUTDOWN
# ============================================================

def start_compact_silently():
    root._starting_compact = True

    try:
        collapse_note()
    finally:
        root._starting_compact = False


def close_app():
    save_data()

    try:
        import pygame

        if pygame.mixer.get_init():
            pygame.mixer.quit()
    except Exception:
        pass

    try:
        if wolf is not None and wolf.winfo_exists():
            wolf.destroy()
    except tk.TclError:
        pass

    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)

root.withdraw()
root.after(500, start_compact_silently)

root.mainloop()

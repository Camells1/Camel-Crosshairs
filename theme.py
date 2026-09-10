import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

FG_DIM = "#937a55"

DANGER = "#c9524a"
DANGER_HI = "#ef8079"

FONT = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_SMALL = ("Segoe UI", 7)
FONT_TITLE = ("Segoe UI", 11, "bold")

# ---- Full per-theme palettes, lifted from Camel Launcher's actual "biome
# matrix" dark ramps (renderer/style.css) so switching themes here changes
# both the background and the accent, the same way it does there. ----
ACCENTS = {
    "desert": {
        "label": "Desert", "accent": "#e8963c", "hi": "#ffc178", "lo": "#ad6620",
        "bg": "#120c07", "rail": "#1a1109", "panel": "#21160c", "card": "#2b1d11",
        "raised": "#382614", "border": "#4a3219", "well": "#170f08", "well_deep": "#150e07",
        "text": "#f8eeda", "text_muted": "#c6a87d", "logo": "logo-ochre.png",
    },
    "oasis": {
        "label": "Oasis", "accent": "#4fa07d", "hi": "#7bc9a5", "lo": "#2c6249",
        "bg": "#0a140d", "rail": "#0f1f14", "panel": "#14291a", "card": "#1a3521",
        "raised": "#23472b", "border": "#2f5c39", "well": "#0c1710", "well_deep": "#0a140d",
        "text": "#eaf5e8", "text_muted": "#a8c9a8", "logo": "logo-oasis.png",
    },
    "clay": {
        "label": "Volcano", "accent": "#c2604a", "hi": "#e8927a", "lo": "#8a3f2e",
        "bg": "#150b09", "rail": "#201210", "panel": "#2a1815", "card": "#38201a",
        "raised": "#4a2a20", "border": "#5f372a", "well": "#180d0a", "well_deep": "#150b09",
        "text": "#f8e8e0", "text_muted": "#c9a290", "logo": "logo-clay.png",
    },
    "azure": {
        "label": "Ocean", "accent": "#4a90c2", "hi": "#7fb8e0", "lo": "#2f5f85",
        "bg": "#081420", "rail": "#0c1e30", "panel": "#10283e", "card": "#15344f",
        "raised": "#1c4666", "border": "#245a80", "well": "#0a1826", "well_deep": "#081420",
        "text": "#e6f2fa", "text_muted": "#9dc2d9", "logo": "logo-azure.png",
    },
    "mauve": {
        "label": "Space", "accent": "#9b6b8f", "hi": "#c79bbd", "lo": "#6b4363",
        "bg": "#100a18", "rail": "#181026", "panel": "#201632", "card": "#2a1e42",
        "raised": "#382958", "border": "#48366e", "well": "#130d1c", "well_deep": "#100a18",
        "text": "#f0e8fa", "text_muted": "#bfa6d9", "logo": "logo-mauve.png",
    },
    "starburst": {
        "label": "Starburst", "accent": "#ffd60a", "hi": "#ffe873", "lo": "#c9a300",
        "bg": "#0a0512", "rail": "#120a1e", "panel": "#190f2a", "card": "#221640",
        "raised": "#301f58", "border": "#402a72", "well": "#08040f", "well_deep": "#05030a",
        "text": "#f7eefc", "text_muted": "#c9aee8", "logo": "logo-starburst.png",
    },
}

ACCENT_NAME = "desert"
ACCENT = ACCENT_HI = ACCENT_LO = None
BG = RAIL = PANEL = CARD = RAISED = CARD_BORDER = WELL = PREVIEW_BG = None
FG = FG_MUTED = None
LOGO_FILE = None


def set_accent(name):
    global ACCENT_NAME, ACCENT, ACCENT_HI, ACCENT_LO
    global BG, RAIL, PANEL, CARD, RAISED, CARD_BORDER, WELL, PREVIEW_BG, FG, FG_MUTED, LOGO_FILE

    entry = ACCENTS.get(name, ACCENTS["desert"])
    ACCENT_NAME = name if name in ACCENTS else "desert"
    ACCENT = entry["accent"]
    ACCENT_HI = entry["hi"]
    ACCENT_LO = entry["lo"]
    BG = entry["bg"]
    RAIL = entry["rail"]
    PANEL = entry["panel"]
    CARD = entry["card"]
    RAISED = entry["raised"]
    CARD_BORDER = entry["border"]
    WELL = entry["well"]
    PREVIEW_BG = entry["well_deep"]
    FG = entry["text"]
    FG_MUTED = entry["text_muted"]
    LOGO_FILE = entry["logo"]


set_accent("desert")


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def gradient_color_at(top_hex, bottom_hex, t):
    """The color a vertical gradient from top_hex to bottom_hex would show
    at fraction t (0=top, 1=bottom) — for blending flat widgets (labels)
    into a gradient panel behind them."""
    t = max(0.0, min(1.0, t))
    tr, tg, tb = _hex_to_rgb(top_hex)
    br, bg_, bb = _hex_to_rgb(bottom_hex)
    r = round(tr + (br - tr) * t)
    g = round(tg + (bg_ - tg) * t)
    b = round(tb + (bb - tb) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def make_gradient_image(width, height, top_hex, bottom_hex):
    width, height = max(1, int(width)), max(1, int(height))
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    tr, tg, tb = _hex_to_rgb(top_hex)
    br, bg_, bb = _hex_to_rgb(bottom_hex)
    for y in range(height):
        t = y / max(1, height - 1)
        r = round(tr + (br - tr) * t)
        g = round(tg + (bg_ - tg) * t)
        b = round(tb + (bb - tb) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def gradient_canvas(parent, width, height, top_hex=None, bottom_hex=None, **kwargs):
    """A Canvas pre-filled with a vertical gradient — the closest Tkinter
    equivalent to Camel Launcher's `.panel` CSS gradient. Returns the Canvas;
    place further content on it with create_window()."""
    top_hex = top_hex or CARD
    bottom_hex = bottom_hex or PANEL
    kwargs.setdefault("highlightthickness", 0)
    kwargs.setdefault("bd", 0)
    cv = tk.Canvas(parent, width=width, height=height, **kwargs)
    img = make_gradient_image(width, height, top_hex, bottom_hex)
    photo = ImageTk.PhotoImage(img)
    cv._gradient_img = photo  # keep a reference alive
    cv.create_image(0, 0, anchor="nw", image=photo)
    return cv


def apply_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=BG)

    style.configure(".", background=BG, foreground=FG, font=FONT)
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("Rail.TFrame", background=RAIL)
    style.configure("TLabel", background=BG, foreground=FG, font=FONT)
    style.configure("Muted.TLabel", background=BG, foreground=FG_MUTED, font=FONT)
    style.configure("Title.TLabel", background=BG, foreground=FG, font=FONT_TITLE)
    style.configure("Panel.TLabel", background=PANEL, foreground=FG, font=FONT)

    style.configure(
        "TButton", background=RAISED, foreground=FG, borderwidth=0,
        focuscolor=RAISED, padding=(10, 6), font=FONT,
    )
    style.map(
        "TButton",
        background=[("active", ACCENT), ("pressed", ACCENT_LO)],
        foreground=[("active", "#2b1608")],
    )

    style.configure(
        "Accent.TButton", background=ACCENT, foreground="#2b1608",
        borderwidth=0, padding=(10, 6), font=FONT_BOLD,
    )
    style.map("Accent.TButton", background=[("active", ACCENT_HI)])

    style.configure(
        "Horizontal.TScale", background=BG, troughcolor=RAISED,
        borderwidth=0, lightcolor=ACCENT, darkcolor=ACCENT,
    )

    style.configure("TCheckbutton", background=BG, foreground=FG, font=FONT, focuscolor=BG)
    style.map("TCheckbutton", background=[("active", BG)])

    style.configure("TRadiobutton", background=BG, foreground=FG, font=FONT, focuscolor=BG)
    style.map("TRadiobutton", background=[("active", BG)])

    style.configure(
        "TCombobox", fieldbackground=WELL, background=WELL, foreground=FG,
        arrowcolor=FG, borderwidth=0, padding=6,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", WELL)],
        selectbackground=[("readonly", WELL)],
        selectforeground=[("readonly", FG)],
    )

    style.configure("Vertical.TScrollbar", background=RAISED, troughcolor=BG, borderwidth=0, arrowsize=12)

    return style


def segmented_button(parent, text, command, active=False):
    btn = tk.Button(
        parent, text=text, command=command, relief="flat", bd=0,
        font=FONT_BOLD, padx=16, pady=6, cursor="hand2",
        bg=ACCENT if active else RAISED, fg="#2b1608" if active else FG_MUTED,
        activebackground=ACCENT_HI, activeforeground="#2b1608",
    )
    return btn


def rail_button(parent, text, command, active=False):
    """A left-rail navigation pill, matching Camel Launcher's icon-rail buttons."""
    btn = tk.Button(
        parent, text=text, command=command, relief="flat", bd=0,
        font=FONT_BOLD, padx=12, pady=10, cursor="hand2", anchor="w",
        bg=ACCENT if active else CARD, fg="#2b1608" if active else FG_MUTED,
        activebackground=ACCENT_HI, activeforeground="#2b1608",
        width=12,
    )
    return btn

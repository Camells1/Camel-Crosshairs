import json
import os
import shutil
import uuid

APP_DATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "CrosshairOverlay")
IMAGES_DIR = os.path.join(APP_DATA, "images")
SETTINGS_PATH = os.path.join(APP_DATA, "settings.json")
CUSTOM_PRESETS_PATH = os.path.join(APP_DATA, "custom_presets.json")

DEFAULTS = {
    "mode": "shape",          # "shape" or "image"
    "shape": "cross",         # cross, cross_dot, dot, x, t, circle
    "color": "#39FF14",
    "outline_color": "#000000",
    "outline_width": 1,
    "size": 10,                # arm length in px
    "thickness": 2,
    "gap": 4,
    "opacity": 1.0,             # 0.05 - 1.0
    "image_path": None,         # absolute path under IMAGES_DIR
    "image_scale": 100,         # percent
    "visible": True,
    "follow_cursor": True,      # track the mouse and replace the OS cursor
    "ui_accent": "desert",      # settings window accent theme
}


def ensure_dirs():
    os.makedirs(APP_DATA, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


def load_settings():
    ensure_dirs()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULTS.copy()
            merged.update(data)
            return merged
        except Exception:
            return DEFAULTS.copy()
    return DEFAULTS.copy()


def save_settings(settings):
    ensure_dirs()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def import_image(src_path):
    """Copy a user-picked image into the app's data dir and return the new path."""
    ensure_dirs()
    ext = os.path.splitext(src_path)[1].lower() or ".png"
    dest = os.path.join(IMAGES_DIR, f"{uuid.uuid4().hex}{ext}")
    shutil.copyfile(src_path, dest)
    return dest


def load_custom_presets():
    ensure_dirs()
    if os.path.exists(CUSTOM_PRESETS_PATH):
        try:
            with open(CUSTOM_PRESETS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def save_custom_presets(presets):
    ensure_dirs()
    with open(CUSTOM_PRESETS_PATH, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2)

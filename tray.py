import os
import sys
import threading

from PIL import Image, ImageDraw
import pystray

import theme


def _asset_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


def make_icon_image():
    try:
        return Image.open(_asset_path(os.path.join("logos", theme.LOGO_FILE))).convert("RGBA")
    except Exception:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        color = (57, 255, 20, 255)
        d.line([(32, 6), (32, 26)], fill=color, width=5)
        d.line([(32, 38), (32, 58)], fill=color, width=5)
        d.line([(6, 32), (26, 32)], fill=color, width=5)
        d.line([(38, 32), (58, 32)], fill=color, width=5)
        d.ellipse([(29, 29), (35, 35)], fill=color)
        return img


class TrayIcon:
    def __init__(self, on_toggle, on_show_settings, on_exit):
        self.icon = pystray.Icon(
            "CamelCrosshairs",
            make_icon_image(),
            "Camel Crosshairs",
            menu=pystray.Menu(
                pystray.MenuItem("Show / Hide Crosshair", lambda: on_toggle()),
                pystray.MenuItem("Open Settings", lambda: on_show_settings()),
                pystray.MenuItem("Quit", lambda: on_exit()),
            ),
        )
        self._thread = threading.Thread(target=self.icon.run, daemon=True)

    def start(self):
        self._thread.start()

    def refresh_icon(self):
        """Call after theme.set_accent(...) changes to match the tray icon
        to the new theme's logo, same as the window/taskbar icon."""
        try:
            self.icon.icon = make_icon_image()
        except Exception:
            pass

    def stop(self):
        try:
            self.icon.stop()
        except Exception:
            pass

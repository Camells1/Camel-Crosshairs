import ctypes
import os
import tkinter as tk
from ctypes import wintypes

import win32api
import win32con
import win32gui
from PIL import Image, ImageTk

import cursor_hide
from crosshair_draw import draw_crosshair

KEY_COLOR = "#010203"  # chroma-key color treated as fully transparent

_CURSOR_SHOWING = 0x00000001


class _CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT),
    ]


def _os_cursor_is_shown():
    """Whether the OS considers the cursor currently visible (the ShowCursor
    show/hide counter), independent of what bitmap it's using. Games
    typically hide this during camera-look play and show it again for
    mouse-driven UI like an inventory screen — the same flag screen-recording
    software checks to decide whether to draw a cursor overlay."""
    try:
        ci = _CURSORINFO()
        ci.cbSize = ctypes.sizeof(_CURSORINFO)
        if not ctypes.windll.user32.GetCursorInfo(ctypes.byref(ci)):
            return True
        return bool(ci.flags & _CURSOR_SHOWING)
    except Exception:
        return True

_LOG_PATH = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "CrosshairOverlay", "debug.log"
)


def _log_error(where, exc, tb_text):
    try:
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{where}] {exc!r}\n{tb_text}\n")
    except Exception:
        pass


def _colorref_from_hex(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return win32api.RGB(r, g, b)


class Overlay:
    """A borderless, always-on-top, click-through window that draws the crosshair."""

    def __init__(self, master, settings):
        self.settings = settings
        self.size = 300
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", KEY_COLOR)
        self.win.config(bg=KEY_COLOR)
        self._position_window()

        self.canvas = tk.Canvas(
            self.win, width=self.size, height=self.size, bg=KEY_COLOR, highlightthickness=0
        )
        self.canvas.pack()
        self._tk_image = None
        self.hwnd = None
        self._tracking = False
        self._screen_w = win32api.GetSystemMetrics(0)
        self._screen_h = win32api.GetSystemMetrics(1)
        self._screen_center = (self._screen_w // 2, self._screen_h // 2)

        self.win.after(50, self._make_click_through)
        # Started independently of _make_click_through so a failure there
        # (e.g. transparency/opacity setup) can never block cursor tracking.
        # _track_loop itself tolerates self.hwnd being unset for a while.
        self.win.after(60, self._start_tracking)
        self.draw()

        if not settings.get("visible", True):
            self.win.withdraw()

    def _position_window(self):
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = sw // 2 - self.size // 2
        y = sh // 2 - self.size // 2
        self.win.geometry(f"{self.size}x{self.size}+{x}+{y}")

    def _resolve_hwnd(self):
        """GetParent can return 0 if the window isn't fully mapped by the OS
        yet (observed specifically in the frozen exe, where startup timing
        differs from running from source). Force realization and validate."""
        self.win.update_idletasks()
        wid = self.win.winfo_id()
        hwnd = win32gui.GetParent(wid)
        if not hwnd or not win32gui.IsWindow(hwnd):
            hwnd = wid
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None
        return hwnd

    def _make_click_through(self, attempt=0):
        try:
            hwnd = self._resolve_hwnd()
            if not hwnd:
                if attempt < 40:
                    self.win.after(50, lambda: self._make_click_through(attempt + 1))
                return
            self.hwnd = hwnd
            styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            styles |= (
                win32con.WS_EX_LAYERED
                | win32con.WS_EX_TRANSPARENT
                | win32con.WS_EX_TOOLWINDOW
            )
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles)
            self._apply_opacity()
            self._sync_cursor_state()
        except Exception:
            if attempt < 40:
                self.win.after(50, lambda: self._make_click_through(attempt + 1))

    def _sync_cursor_state(self):
        """Hide/show the real OS cursor to match follow-cursor + visibility."""
        should_hide = self.settings.get("follow_cursor", True) and self.settings.get("visible", True)
        if should_hide and not cursor_hide.is_hidden():
            cursor_hide.hide_system_cursor()
        elif not should_hide and cursor_hide.is_hidden():
            cursor_hide.restore_system_cursor()

    def _start_tracking(self):
        if self._tracking:
            return
        self._tracking = True
        self._track_loop()

    def _foreground_is_fullscreen(self):
        """True when the focused window covers the whole monitor — the
        standard, widely-used signal ("is a game running") that taskbar
        auto-hide and every game-bar/overlay tool relies on. Just a focus +
        size check; nothing about the cursor is inspected here."""
        try:
            fg = win32gui.GetForegroundWindow()
            if not fg or fg == self.hwnd:
                return False
            l, t, r, b = win32gui.GetWindowRect(fg)
            return (r - l) >= self._screen_w - 2 and (b - t) >= self._screen_h - 2
        except Exception:
            return False

    def _track_loop(self):
        try:
            follow = self.settings.get("follow_cursor", True)
            visible = self.settings.get("visible", True)
            if visible and self.hwnd:
                half = self.size // 2
                if follow:
                    if self._foreground_is_fullscreen() and not _os_cursor_is_shown():
                        # A fullscreen game is focused AND it has hidden the
                        # OS cursor — the camera-look state, where games
                        # handle cursor position too inconsistently (frozen,
                        # drifting, recentered) to track reliably. Pin center.
                        x, y = self._screen_center
                    else:
                        # Desktop, or a fullscreen game showing the cursor
                        # again for mouse-driven UI (e.g. an inventory
                        # screen) — follow it like normal.
                        x, y = win32api.GetCursorPos()
                    px, py = x - half, y - half
                else:
                    px, py = None, None
                # Re-assert HWND_TOPMOST every tick (not just SWP_NOZORDER) so
                # the crosshair can't lose its top position to the taskbar or
                # any other window that grabs topmost after us. Also keeps
                # reasserting when not following the cursor, so a fixed
                # center crosshair can't get buried either.
                if px is not None:
                    win32gui.SetWindowPos(
                        self.hwnd, win32con.HWND_TOPMOST, px, py, 0, 0,
                        win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                    )
                else:
                    win32gui.SetWindowPos(
                        self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOSIZE | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE,
                    )
        except Exception as e:
            import traceback
            _log_error("track_loop", e, traceback.format_exc())
        self.win.after(10, self._track_loop)

    def _apply_opacity(self):
        # IMPORTANT: color-key transparency and alpha blending share the same
        # underlying Win32 layered-window attributes. Setting alpha alone
        # (LWA_ALPHA only) silently drops the color key, turning the
        # "transparent" background into a solid opaque box. Both flags must
        # always be set together in the same call.
        try:
            hwnd = self.hwnd or self._resolve_hwnd()
            if not hwnd:
                return
            alpha = int(max(0.05, min(1.0, self.settings.get("opacity", 1.0))) * 255)
            crkey = _colorref_from_hex(KEY_COLOR)
            win32gui.SetLayeredWindowAttributes(
                hwnd, crkey, alpha, win32con.LWA_COLORKEY | win32con.LWA_ALPHA
            )
        except Exception:
            pass

    def show(self):
        self.win.deiconify()
        self.settings["visible"] = True
        self.win.after(30, self._make_click_through)
        self._sync_cursor_state()

    def hide(self):
        self.win.withdraw()
        self.settings["visible"] = False
        self._sync_cursor_state()

    def toggle(self):
        if self.settings.get("visible", True):
            self.hide()
        else:
            self.show()

    def refresh(self):
        """Re-read settings and redraw (call after any settings change)."""
        self._apply_opacity()
        self._sync_cursor_state()
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        c = self.size // 2
        if self.settings.get("mode") == "image" and self.settings.get("image_path"):
            ok = self._draw_image(c)
            if not ok:
                self._draw_shape(c)
        else:
            self._draw_shape(c)

    def _draw_image(self, c):
        try:
            img = Image.open(self.settings["image_path"]).convert("RGBA")
            scale = max(1, self.settings.get("image_scale", 100)) / 100.0
            w = max(1, int(img.width * scale))
            h = max(1, int(img.height * scale))
            if w > self.size or h > self.size:
                ratio = min(self.size / w, self.size / h)
                w = max(1, int(w * ratio))
                h = max(1, int(h * ratio))
            img = img.resize((w, h), Image.LANCZOS)
            self._tk_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(c, c, image=self._tk_image)
            return True
        except Exception:
            return False

    def _draw_shape(self, c):
        s = self.settings
        draw_crosshair(
            self.canvas, c, c,
            shape=s.get("shape", "cross"),
            color=s.get("color", "#39FF14"),
            outline_color=s.get("outline_color", ""),
            outline_width=s.get("outline_width", 0),
            size=s.get("size", 10),
            thickness=s.get("thickness", 2),
            gap=s.get("gap", 4),
        )

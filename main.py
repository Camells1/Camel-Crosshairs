import atexit
import ctypes
import queue
import tkinter as tk

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import config
import cursor_hide
import theme
from overlay import Overlay
from settings_window import SettingsWindow
from tray import TrayIcon

command_queue = queue.Queue()

# Safety net: no matter how the process ends, never leave the user's real
# mouse cursor permanently invisible system-wide.
atexit.register(cursor_hide.restore_system_cursor)


def main():
    settings = config.load_settings()
    theme.set_accent(settings.get("ui_accent", "desert"))

    root = tk.Tk()
    root.withdraw()

    overlay = Overlay(root, settings)

    def on_change(new_settings):
        config.save_settings(new_settings)

    def toggle_crosshair():
        command_queue.put(("toggle",))

    def show_settings():
        command_queue.put(("show_settings",))

    def exit_app():
        command_queue.put(("exit",))

    def toggle_follow():
        command_queue.put(("toggle_follow",))

    def get_follow_state():
        return settings.get("follow_cursor", True)

    tray = TrayIcon(
        on_toggle=toggle_crosshair,
        on_show_settings=show_settings,
        on_exit=exit_app,
        on_toggle_follow=toggle_follow,
        get_follow_state=get_follow_state,
    )
    tray.start()

    settings_win = SettingsWindow(
        root, settings, overlay,
        on_change=on_change,
        on_exit=exit_app,
        on_accent_change=tray.refresh_icon,
    )

    def poll_queue():
        try:
            while True:
                cmd = command_queue.get_nowait()
                if cmd[0] == "toggle":
                    overlay.toggle()
                    settings_win.visible_var.set(settings.get("visible", True))
                    config.save_settings(settings)
                elif cmd[0] == "toggle_follow":
                    settings["follow_cursor"] = not settings.get("follow_cursor", True)
                    overlay.refresh()
                    settings_win.follow_cursor_var.set(settings["follow_cursor"])
                    config.save_settings(settings)
                elif cmd[0] == "show_settings":
                    settings_win.show()
                elif cmd[0] == "exit":
                    config.save_settings(settings)
                    tray.stop()
                    cursor_hide.restore_system_cursor()
                    root.after(50, root.destroy)
                    return
        except queue.Empty:
            pass
        root.after(100, poll_queue)

    root.after(100, poll_queue)

    settings_win.show()
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    finally:
        cursor_hide.restore_system_cursor()

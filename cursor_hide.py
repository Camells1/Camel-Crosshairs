"""Replaces the Windows system cursor with a blank one, system-wide, so the
overlay crosshair can act as the visible pointer everywhere (desktop, menus,
and in-game where the OS cursor is shown). Always restore on exit.
"""
import ctypes

user32 = ctypes.windll.user32

SPI_SETCURSORS = 0x0057

# All standard system cursor IDs (OCR_*)
_OCR_IDS = [
    32512,  # NORMAL
    32513,  # IBEAM
    32514,  # WAIT
    32515,  # CROSS
    32516,  # UP
    32640,  # SIZE
    32641,  # ICON
    32642,  # SIZENWSE
    32643,  # SIZENESW
    32644,  # SIZEWE
    32645,  # SIZENS
    32646,  # SIZEALL
    32648,  # NO
    32649,  # HAND
    32650,  # APPSTARTING
    32651,  # HELP
]

_hidden = False


def _make_blank_cursor():
    w, h = 32, 32
    nbytes = (w // 8) * h
    and_mask = (ctypes.c_ubyte * nbytes)(*([0xFF] * nbytes))  # fully transparent
    xor_mask = (ctypes.c_ubyte * nbytes)(*([0x00] * nbytes))
    return user32.CreateCursor(0, 0, 0, w, h, and_mask, xor_mask)


def hide_system_cursor():
    global _hidden
    try:
        for ocr_id in _OCR_IDS:
            h = _make_blank_cursor()
            if h:
                user32.SetSystemCursor(h, ocr_id)
        _hidden = True
    except Exception:
        pass


def restore_system_cursor():
    global _hidden
    try:
        user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)
    except Exception:
        pass
    _hidden = False


def is_hidden():
    return _hidden

"""Hilfen für das Konsolenfenster unter Windows."""

import sys


def quickedit_aus() -> None:
    """Schaltet unter Windows den „QuickEdit-Modus“ des Konsolenfensters ab.

    Sonst hält ein Mausklick ins Fenster (Text markieren) das Programm an, bis Esc oder Enter
    gedrückt wird – SPS-Simulator, Vision-Dienst oder Live-Ansicht reagieren dann nicht mehr
    (OPC-UA-Zeitüberschreitung). Ohne Konsole oder unter Linux passiert nichts.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return
        enable_quick_edit, enable_extended_flags = 0x0040, 0x0080
        kernel32.SetConsoleMode(handle, (mode.value & ~enable_quick_edit) | enable_extended_flags)
    except Exception:  # nur Komfort – nie den Start verhindern
        pass

"""
Folder Picker Module
Provides GUI folder selection dialogs for Local Repo Path:
1. Native OS Folder Picker (via Zenity on Ubuntu/GNOME, or Tkinter as fallback)
2. In-App Interactive Directory Browser (works seamlessly in any browser/remote environment)
"""

import os
import shutil
import subprocess
from typing import List, Optional, Tuple


def pick_folder_native(initial_dir: Optional[str] = None) -> Optional[str]:
    """
    Opens native OS GUI directory selection dialog.
    Prioritizes Zenity on Linux (native GTK dialog), falls back to Tkinter.
    Returns selected path string or None if cancelled.
    """
    start_dir = initial_dir or os.getcwd()

    # 1. Try Zenity on Linux/Ubuntu if DISPLAY or WAYLAND_DISPLAY is available
    has_display = bool(os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"))
    if has_display and shutil.which("zenity"):
        try:
            cmd = [
                "zenity",
                "--file-selection",
                "--directory",
                f"--filename={os.path.abspath(start_dir)}/",
                "--title=Select Local Git Repository",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                selected = res.stdout.strip()
                if selected and os.path.isdir(selected):
                    return os.path.abspath(selected)
            elif res.returncode == 1:
                # User pressed Cancel
                return None
        except Exception:
            pass

    # 2. Try Tkinter filedialog
    if has_display:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.wm_attributes("-topmost", 1)
            selected = filedialog.askdirectory(
                initialdir=start_dir,
                title="Select Local Git Repository",
            )
            root.destroy()
            if selected and os.path.isdir(selected):
                return os.path.abspath(selected)
        except Exception:
            pass

    return None


def list_directory_entries(dir_path: str) -> Tuple[List[str], bool]:
    """
    Returns a sorted list of subdirectories in dir_path and whether dir_path has a .git folder.
    """
    abs_path = os.path.abspath(dir_path)
    subdirs = []
    has_git = os.path.exists(os.path.join(abs_path, ".git"))

    try:
        entries = os.listdir(abs_path)
        for e in entries:
            # Skip hidden folders
            if e.startswith("."):
                continue
            full_path = os.path.join(abs_path, e)
            if os.path.isdir(full_path):
                is_sub_git = os.path.exists(os.path.join(full_path, ".git"))
                subdirs.append((e, is_sub_git))
    except (PermissionError, FileNotFoundError):
        pass

    # Sort alphabetically
    subdirs.sort(key=lambda x: x[0].lower())
    return subdirs, has_git

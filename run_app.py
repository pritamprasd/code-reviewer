"""
Standalone Desktop / Binary Launcher for AI Code Reviewer Streamlit App.
Used for standalone packaging and Ubuntu desktop deployment.
"""

import os
import sys
import webbrowser
import threading
import time
import streamlit.web.cli as stcli


def open_browser_after_start():
    time.sleep(2.0)
    webbrowser.open("http://localhost:8501")


def main():
    # Resolve directory paths whether running from source or frozen binary
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "app.py")

    # Start browser opener in background thread
    threading.Thread(target=open_browser_after_start, daemon=True).start()

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
        "--server.port=8501",
        "--browser.serverAddress=localhost",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()

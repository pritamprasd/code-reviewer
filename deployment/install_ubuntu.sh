#!/usr/bin/env bash
set -e

echo "=============================================="
echo " Installing AI Code Reviewer Agent on Ubuntu "
echo "=============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# 1. Check Python & Git
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is not installed. Please run: sudo apt update && sudo apt install -y python3 python3-venv python3-pip git"
    exit 1
fi

if ! command -v git &>/dev/null; then
    echo "Error: Git is not installed. Please run: sudo apt install -y git"
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing / updating dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Register Desktop Launcher
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat <<EOF > "$DESKTOP_DIR/code-reviewer.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=AI Code Reviewer
Comment=Offline AI Code Reviewer Streamlit App
Exec=bash -c "cd '$SCRIPT_DIR' && source venv/bin/activate && python3 run_app.py"
Icon=text-editor
Terminal=false
Categories=Development;
StartupNotify=true
EOF

chmod +x "$DESKTOP_DIR/code-reviewer.desktop"
echo "✓ Desktop shortcut registered at: $DESKTOP_DIR/code-reviewer.desktop"

echo "=============================================="
echo " Installation Complete!"
echo " Launch the app by running:"
echo "   source venv/bin/activate && python3 run_app.py"
echo " Or find 'AI Code Reviewer' in your Ubuntu applications menu!"
echo "=============================================="

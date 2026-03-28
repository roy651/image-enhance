#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Image Enhance — setup ==="
echo ""

# Ensure Python 3.11 + Tcl/Tk are available (torch is not compatible with Python 3.12+)
echo "Checking Python 3.11..."
brew install python@3.11 python-tk@3.11
PYTHON311="$(brew --prefix python@3.11)/bin/python3.11"

# Install uv if missing
if ! command -v uv &>/dev/null && [ ! -f "$HOME/.local/bin/uv" ]; then
    echo "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# Install Python dependencies
echo "Installing Python dependencies (this may take a few minutes on first run)..."
uv sync --python "$PYTHON311"
echo ""

# Download models
mkdir -p models

download_if_missing() {
    local url="$1"
    local dest="$2"
    local name
    name="$(basename "$dest")"
    if [ -f "$dest" ]; then
        echo "  $name — already downloaded, skipping"
    else
        echo "  Downloading $name..."
        curl -L --progress-bar "$url" -o "$dest"
    fi
}

echo "Downloading AI models (~550 MB total)..."
download_if_missing \
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth" \
    "models/RealESRGAN_x2plus.pth"
download_if_missing \
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth" \
    "models/RealESRGAN_x4plus.pth"
download_if_missing \
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth" \
    "models/GFPGANv1.4.pth"
echo ""

# Create ImageEnhance.app using osacompile (produces a native arm64 binary, no Rosetta prompt)
echo "Creating ImageEnhance.app..."
rm -rf "$SCRIPT_DIR/ImageEnhance.app"
TMPSCRIPT=$(mktemp /tmp/launcher_XXXXXX.applescript)
cat > "$TMPSCRIPT" <<APPLESCRIPT
do shell script "cd '${SCRIPT_DIR}' && '${SCRIPT_DIR}/.venv/bin/python' '${SCRIPT_DIR}/app.py' > /tmp/image-enhance.log 2>&1 &"
APPLESCRIPT
osacompile -o "$SCRIPT_DIR/ImageEnhance.app" "$TMPSCRIPT"
rm "$TMPSCRIPT"

echo "=== Setup complete ==="
echo ""
echo "Double-click ImageEnhance.app to launch."
echo "(You can move it to your Desktop or Applications folder — it will still work.)"

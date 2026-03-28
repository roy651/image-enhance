#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Image Enhance — setup ==="
echo ""

# Install uv if missing
if ! command -v uv &>/dev/null && [ ! -f "$HOME/.local/bin/uv" ]; then
    echo "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# Install Python dependencies
echo "Installing Python dependencies (this may take a few minutes on first run)..."
uv sync
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

# Create ImageEnhance.app bundle
APP="$SCRIPT_DIR/ImageEnhance.app"
MACOS_DIR="$APP/Contents/MacOS"
mkdir -p "$MACOS_DIR"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ImageEnhance</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.image-enhance</string>
    <key>CFBundleName</key>
    <string>Image Enhance</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

cat > "$MACOS_DIR/ImageEnhance" <<LAUNCHER
#!/bin/bash
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/app.py"
LAUNCHER

chmod +x "$MACOS_DIR/ImageEnhance"

echo "=== Setup complete ==="
echo ""
echo "Double-click ImageEnhance.app to launch."
echo "(You can move it to your Desktop or Applications folder — it will still work.)"

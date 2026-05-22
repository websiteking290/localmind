#!/bin/bash
# =================================================================
#  LocalMind macOS App Bundle Creator
#  Wraps the launcher in a native .app bundle
# =================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="LocalMind"
BUNDLE_ID="ai.localmind.launcher"
VERSION="1.0.0"

# ── Create App Structure ─────────────────────────────────
APP_DIR="$USB_ROOT/${APP_NAME}.app"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

log() { echo "[LocalMind] $*"; }

log "Creating macOS app bundle..."

# Clean old
rm -rf "$APP_DIR"

# Create directories
mkdir -p "$MACOS" "$RESOURCES"

# ── Info.plist ─────────────────────────────────────────────
cat > "$CONTENTS/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>English</string>
  <key>CFBundleExecutable</key>
  <string>LocalMind</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundleIdentifier</key>
  <string>$BUNDLE_ID</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>$VERSION</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
EOF

# ── Launcher Script ───────────────────────────────────────
cat > "$MACOS/LocalMind" << 'EOF'
#!/bin/bash
# LocalMind Launcher — macOS App Bundle Entry Point

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LAUNCHER_DIR="$USB_ROOT/launcher"
LAUNCHER_PY="$LAUNCHER_DIR/launcher.py"

# Show dock icon (macOS specific)
export PYTHONUNBUFFERED=1

# Find Python
PYTHON_EXE=""
if [ -f "$LAUNCHER_DIR/python/bin/python3" ]; then
    PYTHON_EXE="$LAUNCHER_DIR/python/bin/python3"
elif command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
elif command -v python &> /dev/null; then
    PYTHON_EXE="python"
fi

if [ -z "$PYTHON_EXE" ]; then
    osascript -e 'display dialog "Python 3 is required to run LocalMind. Please install it from python.org." buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Run launcher
exec "$PYTHON_EXE" "$LAUNCHER_PY"
EOF
chmod +x "$MACOS/LocalMind"

# ── Create Icon (placeholder) ───────────────────────────────
# In production, you'd convert a PNG to .icns format
# For now, we'll use a simple approach
ICON_PNG="$RESOURCES/AppIcon.png"
if [ ! -f "$ICON_PNG" ]; then
  # Create a simple colored icon using Python/Pillow or just a placeholder
  log "Creating app icon placeholder..."
  cat > "$RESOURCES/AppIcon.txt" << 'EOF'
App Icon
========
Replace Resources/AppIcon.icns with a proper macOS icon.

To generate from a PNG:
  1. Create 1024x1024 PNG
  2. Use iconutil or sips to create .icns
  3. Replace Resources/AppIcon.icns
EOF
fi

# ── Set Permissions ───────────────────────────────────────
chmod -R 755 "$APP_DIR"

log "App bundle created: ${APP_NAME}.app"
echo ""
echo "  To test: Double-click ${APP_NAME}.app"
echo "  To distribute: Include ${APP_NAME}.app in the USB root"
echo ""

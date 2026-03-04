#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DEST="$HOME/Applications/MacSnap.app"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.macsnap.plist"

echo "==> Installing dependencies..."
pip3 install rumps pynput pyinstaller --quiet

echo "==> Building MacSnap.app..."
cd "$SCRIPT_DIR"
rm -rf build dist
pyinstaller MacSnap.spec --noconfirm --clean 2>&1 | tail -5

if [ ! -d "$SCRIPT_DIR/dist/MacSnap.app" ]; then
    echo "ERROR: Build failed. Run manually to see full output:"
    echo "  cd $SCRIPT_DIR && pyinstaller MacSnap.spec --noconfirm --clean"
    exit 1
fi

echo "==> Installing MacSnap.app to ~/Applications/..."
mkdir -p "$HOME/Applications"
rm -rf "$APP_DEST"
cp -r "$SCRIPT_DIR/dist/MacSnap.app" "$APP_DEST"

APP_BINARY="$APP_DEST/Contents/MacOS/MacSnap"

echo "==> Setting up auto-start LaunchAgent..."
mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macsnap</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_BINARY</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/macsnap.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/macsnap.error.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo ""
echo "MacSnap is running!  (shows as 'MacSnap', not 'python3.13')"
echo ""
echo "  Hotkeys (configurable from menu):"
echo "    Ctrl+Shift+3  Full screenshot"
echo "    Ctrl+Shift+4  Area selection"
echo "    Ctrl+Shift+5  Window capture"
echo ""
echo "  Screenshots saved to: ~/Screenshots/"
echo ""
echo "  IMPORTANT: Grant Accessibility permission to use hotkeys:"
echo "  System Settings > Privacy & Security > Accessibility"
echo "  Add MacSnap and toggle it ON."
echo ""
echo "  To uninstall: bash uninstall.sh"

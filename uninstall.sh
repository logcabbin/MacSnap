#!/bin/bash
PLIST="$HOME/Library/LaunchAgents/com.macsnap.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
rm -rf "$HOME/Applications/MacSnap.app"
echo "MacSnap uninstalled. The ~/Screenshots folder and ~/.macsnap.json were left intact."

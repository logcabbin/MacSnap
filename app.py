#!/usr/bin/env python3
"""
MacSnap - Lightweight macOS screenshot app
Menu bar icon, global hotkeys, resolution scaling, low file size JPEG output.
"""

import rumps
import subprocess
import os
import json
import datetime
import threading
from pathlib import Path

try:
    from AppKit import NSPasteboard, NSImage
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

try:
    from pynput import keyboard as pynput_keyboard
    HOTKEYS_AVAILABLE = True
except ImportError:
    HOTKEYS_AVAILABLE = False

# ── Configuration ──────────────────────────────────────────────────────────────
SAVE_DIR     = Path.home() / "Screenshots"
CONFIG_FILE  = Path.home() / ".macsnap.json"
MENU_ICON    = "📷"

# Scale options: display label → percentage (applied after capture via sips)
SCALE_OPTIONS = {
    "100%  (full res)": 100,
    "75%": 75,
    "50%  (recommended)": 50,
    "25%  (smallest)": 25,
}
DEFAULT_SCALE = 100   # percent

# Quality options: display label → JPEG quality value
QUALITY_OPTIONS = {
    "95  (best)": 95,
    "75  (recommended)": 75,
    "50": 50,
    "25  (smallest)": 25,
}
DEFAULT_QUALITY = 75

# Default hotkeys (human-readable, stored in config)
DEFAULT_HOTKEYS = {
    "full":   "ctrl+shift+3",
    "area":   "ctrl+shift+4",
    "window": "ctrl+shift+5",
}
# ───────────────────────────────────────────────────────────────────────────────


def _to_pynput(combo: str) -> str:
    """'ctrl+shift+3' → '<ctrl>+<shift>+3'"""
    modifiers = {"ctrl", "shift", "alt", "cmd"}
    parts = [f"<{p}>" if p.strip().lower() in modifiers else p.strip()
             for p in combo.lower().split("+")]
    return "+".join(parts)


def _from_pynput(hk: str) -> str:
    """'<ctrl>+<shift>+3' → 'ctrl+shift+3'"""
    return hk.replace("<", "").replace(">", "")


def _display(combo: str) -> str:
    """'ctrl+shift+3' → 'Ctrl+Shift+3'"""
    return "+".join(p.capitalize() for p in combo.split("+"))


class MacSnap(rumps.App):
    def __init__(self):
        super().__init__(MENU_ICON, quit_button=None)

        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self._scale     = DEFAULT_SCALE
        self._quality   = DEFAULT_QUALITY
        self._clipboard = False
        self._hotkeys   = self._load_config()
        self._listener  = None

        # Build scale submenu
        self._scale_items = {}
        scale_menu = rumps.MenuItem("Scale")
        for label, pct in SCALE_OPTIONS.items():
            item = rumps.MenuItem(label, callback=self._set_scale)
            if pct == DEFAULT_SCALE:
                item.state = 1
            self._scale_items[label] = item
            scale_menu.add(item)

        # Build quality submenu
        self._quality_items = {}
        quality_menu = rumps.MenuItem("Quality")
        for label, val in QUALITY_OPTIONS.items():
            item = rumps.MenuItem(label, callback=self._set_quality)
            if val == DEFAULT_QUALITY:
                item.state = 1
            self._quality_items[label] = item
            quality_menu.add(item)

        # Build hotkeys submenu
        hotkeys_menu = rumps.MenuItem("Hotkeys")
        self._hk_items = {
            "full":   rumps.MenuItem("", callback=lambda _: self._configure_hotkey("full")),
            "area":   rumps.MenuItem("", callback=lambda _: self._configure_hotkey("area")),
            "window": rumps.MenuItem("", callback=lambda _: self._configure_hotkey("window")),
        }
        for item in self._hk_items.values():
            hotkeys_menu.add(item)
        self._refresh_hk_labels()

        # Screenshot action items (stored so we can update their labels)
        self._action_items = {
            "full":   rumps.MenuItem("", callback=self.screenshot_full),
            "area":   rumps.MenuItem("", callback=self.screenshot_area),
            "window": rumps.MenuItem("", callback=self.screenshot_window),
        }
        self._refresh_action_labels()

        self._clipboard_item = rumps.MenuItem(
            "Copy to Clipboard", callback=self._toggle_clipboard
        )

        self.menu = [
            self._action_items["full"],
            self._action_items["area"],
            self._action_items["window"],
            None,
            scale_menu,
            quality_menu,
            hotkeys_menu,
            self._clipboard_item,
            None,
            rumps.MenuItem("Open Screenshots Folder", callback=self.open_folder),
            None,
            rumps.MenuItem("Quit MacSnap", callback=self.quit_app),
        ]

        if HOTKEYS_AVAILABLE:
            self._start_hotkeys()
        else:
            print("pynput not found — hotkeys disabled. Run: pip3 install pynput")

    # ── Config persistence ─────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        try:
            data = json.loads(CONFIG_FILE.read_text())
            hk = data.get("hotkeys", {})
            return {k: hk.get(k, DEFAULT_HOTKEYS[k]) for k in DEFAULT_HOTKEYS}
        except Exception:
            return dict(DEFAULT_HOTKEYS)

    def _save_config(self):
        CONFIG_FILE.write_text(json.dumps({"hotkeys": self._hotkeys}, indent=2))

    # ── Label helpers ──────────────────────────────────────────────────────────

    def _refresh_action_labels(self):
        labels = {
            "full":   "Full Screen",
            "area":   "Select Area",
            "window": "Select Window",
        }
        for key, item in self._action_items.items():
            item.title = f"{labels[key]}   [{_display(self._hotkeys[key])}]"

    def _refresh_hk_labels(self):
        names = {"full": "Full Screen", "area": "Select Area", "window": "Select Window"}
        for key, item in self._hk_items.items():
            item.title = f"{names[key]}:  {_display(self._hotkeys[key])}"

    # ── Hotkey config dialog ───────────────────────────────────────────────────

    def _configure_hotkey(self, action: str):
        names = {"full": "Full Screen", "area": "Select Area", "window": "Select Window"}
        current = self._hotkeys[action]
        response = rumps.Window(
            title=f"Set Hotkey — {names[action]}",
            message="Enter combo using: ctrl, shift, alt, cmd\nExample:  ctrl+shift+3",
            default_text=current,
            ok="Save",
            cancel="Cancel",
            dimensions=(260, 22),
        ).run()

        if not response.clicked:
            return

        raw = response.text.strip().lower()
        if not raw:
            return

        pynput_fmt = _to_pynput(raw)
        # Basic validation — ensure at least one modifier + one key
        if "+" not in raw or not any(m in raw for m in ("ctrl", "shift", "alt", "cmd")):
            rumps.alert(
                title="Invalid hotkey",
                message="Use at least one modifier (ctrl/shift/alt/cmd) and a key.\nExample: ctrl+shift+3",
                ok="OK",
            )
            return

        self._hotkeys[action] = raw
        self._save_config()
        self._refresh_action_labels()
        self._refresh_hk_labels()
        self._restart_hotkeys()

    # ── Scale ──────────────────────────────────────────────────────────────────

    def _set_scale(self, sender):
        for item in self._scale_items.values():
            item.state = 0
        sender.state = 1
        self._scale = SCALE_OPTIONS[sender.title]

    def _set_quality(self, sender):
        for item in self._quality_items.values():
            item.state = 0
        sender.state = 1
        self._quality = QUALITY_OPTIONS[sender.title]

    # ── Clipboard ──────────────────────────────────────────────────────────────

    def _toggle_clipboard(self, sender):
        self._clipboard = not self._clipboard
        sender.state = int(self._clipboard)

    def _copy_to_clipboard(self, path: str):
        if not CLIPBOARD_AVAILABLE:
            print("AppKit not available — clipboard copy skipped")
            return
        image = NSImage.alloc().initWithContentsOfFile_(path)
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.writeObjects_([image])

    # ── Hotkeys ────────────────────────────────────────────────────────────────

    def _start_hotkeys(self):
        def bg(fn):
            return lambda: threading.Thread(target=fn, daemon=True).start()
        try:
            self._listener = pynput_keyboard.GlobalHotKeys({
                _to_pynput(self._hotkeys["full"]):   bg(self.screenshot_full),
                _to_pynput(self._hotkeys["area"]):   bg(self.screenshot_area),
                _to_pynput(self._hotkeys["window"]): bg(self.screenshot_window),
            })
            self._listener.start()
        except Exception as e:
            print(f"Hotkeys unavailable: {e}")

    def _restart_hotkeys(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
        if HOTKEYS_AVAILABLE:
            self._start_hotkeys()

    # ── Screenshot helpers ─────────────────────────────────────────────────────

    def _filepath(self, prefix: str) -> str:
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return str(SAVE_DIR / f"{prefix}_{ts}.jpg")

    def _process(self, path: str):
        """Resize (if scaled) then apply JPEG quality — both via sips (built-in)."""
        if self._scale != 100:
            result = subprocess.run(
                ["sips", "--getProperty", "pixelWidth", path],
                capture_output=True, text=True,
            )
            for line in result.stdout.splitlines():
                if "pixelWidth" in line:
                    orig_w = int(line.split(":")[1].strip())
                    new_w = max(1, int(orig_w * self._scale / 100))
                    subprocess.run(
                        ["sips", "--resampleWidth", str(new_w), path],
                        capture_output=True,
                    )
                    break

        subprocess.run(
            ["sips", "--setProperty", "formatOptions", str(self._quality), path],
            capture_output=True,
        )

    def _notify(self, path: str):
        if not os.path.exists(path):
            return  # user cancelled (Escape during area/window pick)
        self._process(path)
        if self._clipboard:
            self._copy_to_clipboard(path)
        kb = os.path.getsize(path) / 1024
        extras = "  •  Copied to clipboard" if self._clipboard else ""
        rumps.notification(
            title="Screenshot saved",
            subtitle=f"{kb:.0f} KB  •  {self._scale}% scale{extras}",
            message=os.path.basename(path),
            sound=False,
        )

    # ── Actions ────────────────────────────────────────────────────────────────

    def screenshot_full(self, _=None):
        path = self._filepath("full")
        subprocess.run(["screencapture", "-t", "jpg", "-x", path])
        self._notify(path)

    def screenshot_area(self, _=None):
        path = self._filepath("area")
        subprocess.run(["screencapture", "-i", "-t", "jpg", "-x", path])
        self._notify(path)

    def screenshot_window(self, _=None):
        path = self._filepath("window")
        subprocess.run(["screencapture", "-W", "-t", "jpg", "-x", path])
        self._notify(path)

    def open_folder(self, _=None):
        subprocess.run(["open", str(SAVE_DIR)])

    def quit_app(self, _=None):
        if self._listener:
            self._listener.stop()
        rumps.quit_application()


if __name__ == "__main__":
    MacSnap().run()

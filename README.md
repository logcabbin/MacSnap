# MacSnap

Lightweight macOS menu bar screenshot app. Low file size by default — built for humans and AI alike.

![macOS](https://img.shields.io/badge/macOS-11%2B-blue) ![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **📷 Menu bar icon** — always accessible, no Dock clutter
- **Global hotkeys** — capture without switching apps (configurable)
- **Resolution scaling** — 100% / 75% / 50% / 25%
- **JPEG quality control** — 95 / 75 / 50 / 25
- **Copy to clipboard** — optional, fires after every capture
- **Auto-start on login** — via macOS LaunchAgent
- **Proper app name** — shows as *MacSnap*, not *python3.13*

---

## Install

```bash
git clone https://github.com/void-pulse/MacSnap.git
cd MacSnap
bash install.sh
```

Then grant **Accessibility** permission so hotkeys work:
> System Settings → Privacy & Security → Accessibility → add MacSnap → ON

---

## Default Hotkeys

| Action | Hotkey |
|---|---|
| Full Screen | `Ctrl+Shift+3` |
| Select Area | `Ctrl+Shift+4` |
| Select Window | `Ctrl+Shift+5` |

All hotkeys are remappable from the menu (Menu → Hotkeys).

---

## Reduce AI Vision Token Costs

Screenshots sent to vision models (Claude, GPT-4o, Gemini, etc.) are tiled internally — a full 1920×1080 image can consume **3+ tiles** per API call. Scaling down before sending cuts costs significantly with minimal loss of readability for most UI and code tasks.

| Scale | Resolution | Approx. Tiles | Token Saving |
|---|---|---|---|
| 100% | 1920×1080 | ~3 tiles | baseline |
| 75% | 1440×810 | ~1 tile | **~60–70% fewer tokens** |
| 50% | 960×540 | ~1 tile | **~70–80% fewer tokens** |

> A 75% scale on a 1920×1080 screen gives you 1440×810 — dropping from ~3 tiles to ~1 tile, roughly cutting vision token cost by 60–70% for that image. For workflows that send dozens of screenshots per session, this adds up fast.

Use **Menu → Scale → 75%** as a default for AI workflows. Text and UI elements remain readable at this resolution, while token usage drops dramatically.

---

## Screenshots

Screenshots are saved to `~/Screenshots/` as timestamped JPEGs:

```
full_2026-03-04_14-32-01.jpg
area_2026-03-04_14-35-22.jpg
```

---

## Uninstall

```bash
bash uninstall.sh
```

---

## Wiki

Full documentation: [github.com/void-pulse/MacSnap/wiki](https://github.com/void-pulse/MacSnap/wiki)

---

## Requirements

- macOS 11+
- Python 3.9+
- `rumps`, `pynput`, `pyinstaller` (installed automatically by `install.sh`)

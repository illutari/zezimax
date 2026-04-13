# Zezimax

## Overview

Zezimax is a Python-based image detection bot for *Old School RuneScape* (OSRS) using the RuneLite client. The script provides core automation capabilities including window recognition, pixel/color detection, and simulated mouse/keyboard input.

Designed specifically for Linux environments (KDE Plasma on Kubuntu), the bot features a simple graphical user interface (GUI) for easy control. It demonstrates fundamental botting mechanics: selecting the game window, locating specific pixel colors on-screen, performing clicks, and responding to visual state changes.

**Current functionality (Phase 1):**
- Select and focus the RuneLite client window.
- Detect a target pixel color (`#FF00FAFF`) and left-click it.
- Monitor the four screen corners for a specific color (`#61FF5700`).
- Right-click at screen center when the condition is met.
- Automatically terminate after one complete cycle (future expansions will include inventory detection and looped operation).

## Features

- **Graphical Control Panel** with dedicated buttons for window selection, start, and stop.
- **Global Hotkeys** (has to be run as root to work):
  - `F11` – Start the bot.
  - `F12` – Stop the bot.
- **Window Management** via `xdotool` (Linux-native).
- **Fast Screenshot Capture** using `mss`.
- **Precise Pixel Matching** for target and monitor colors.
- **Threaded Operation** to keep the GUI responsive.
- Fully compatible with Kubuntu/KDE Plasma (X11 session required).

## Prerequisites

- **Operating System**: Kubuntu (or any Linux distribution with KDE Plasma and X11).
- **RuneLite Client**: Running in windowed or borderless windowed mode.
- **Required System Package**:
``` bash
sudo apt update
sudo apt install xdotool
```
- **Python Packages**:
``` bash
pip install mss pillow keyboard opencv-python numpy
```
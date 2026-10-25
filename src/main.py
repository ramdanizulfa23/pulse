#!/usr/bin/env python3
"""Pulse — native Linux living-notch panel (GTK4).

Entry point: the tray icon appears, and the floating panel sits near the
top of the screen. Hover to expand, click the tray to toggle.
"""

from __future__ import annotations
import os
import sys
import json
import signal
import argparse
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gio", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GObject, GLib, Adw

from app import PulseApp
from config import DEFAULTS

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Read config.json into a plain dict for the CLI entry point."""
    cfg = dict(DEFAULTS)
    try:
        if path.exists():
            cfg.update(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:
        print(f"[Pulse] config read failed: {exc}", file=sys.stderr)
    cfg["zoom"] = float(cfg.get("zoom", 1.0))
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pulse Linux living notch")
    parser.add_argument(
        "--mode", choices=["gtk", "off"], help="run mode (gtk | off)"
    )
    parser.add_argument(
        "--no-tray", action="store_true", help="do not create a system tray icon"
    )
    parser.add_argument(
        "--debug", action="store_true", help="enable GLib debug output"
    )
    args = parser.parse_args(argv)

    if args.debug:
        GLib.set_prgname("nusa")
        GLib.setenv("G_MESSAGES_DEBUG", "all", overwrite=True)

    cfg = load_config(CONFIG_PATH)
    if args.mode:
        cfg["mode"] = args.mode

    # GTK4: Gtk.init() takes no arguments and must be called before any
    # Gtk widget is created.
    Gtk.init()

    app = PulseApp()
    app.set_property("application-id", "com.x.Pulse")

    if not args.no_tray:
        import tray
        tray.attach(app)

    # Touch/positioning is attached once the panel window exists, which
    # happens inside do_activate when app.run() starts.
    if cfg["mode"] == "overlay":
        print(
            "[Pulse] overlay mode requested (shell extension required)",
            file=sys.stderr,
        )
    else:
        print(f"[Pulse] running in gtk mode (zoom={cfg['zoom']})", file=sys.stderr)

    # app.run() blocks until the application is quit (Ctrl+Q / tray Quit).
    app.run([])

    print("[Pulse] stopped", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

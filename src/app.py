"""Pulse application core."""

from __future__ import annotations

import os
import sys
import json
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

import cairo
from panel import PulsePanel

from config import config
from face import CatFace
import musik, pomo, volume, lyrics as lrc


class PulseApp(Adw.Application):
    """Main application object: model, window, tray."""

    __gtype_name__ = "PulseApp"

    def __init__(self) -> None:
        super().__init__(application_id="com.x.Pulse")
        self.window: PulsePanel | None = None
        self._visible = False
        self._music = musik.detect()
        self._mood = "idle"
        self._frame = 0
        self._hold_items = []
        self._pomo = pomo.Pomodoro()
        self._vol = (
            volume.PulseAudioSource()
            if config.volume
            else volume.MockVolumeSource()
        )
        self._lyrics = None
        # Resolve resource paths early (needed if we ever open file data).
        self.set_resource_base_path(str(Path(__file__).resolve().parent))

    def do_activate(self) -> None:
        self.window = PulsePanel(self)
        self.window.set_visible(True)
        self.window.position_panel()
        self.window.show_all()

    def toggle_panel(self) -> None:
        if self.window is None:
            return
        if not self._visible:
            self.show_panel()
        else:
            self.hide_panel()

    def show_panel(self) -> None:
        self._visible = True
        self.state = "active"
        if self.window:
            self.window.present()
            GLib.idle_add(self.window.redraw, priority=GLib.PRIORITY_HIGH_IDLE)

    def hide_panel(self) -> None:
        self._visible = False
        self.state = "idle"
        if self.window:
            self.window.hide()

    def quit_gracefully(self) -> None:
        self.quit()

    def screen_rect(self) -> Gdk.Rectangle:
        screens = Gdk.Display.get_default().get_screens()
        if not screens:
            return Gdk.Rectangle()
        rect = None
        for s in screens:
            geom = s.get_geometry()
            if rect is None or geom.width > rect.width:
                rect = geom
        return rect or Gdk.Rectangle()

    def position_panel(self) -> None:
        if self.window is None:
            return
        scr = self.screen_rect()
        self.window.set_position(Gtk.WindowPosition.LEFT)
        self.window.set_default_size(
            int(scr.width * 0.28), int(scr.height * 0.36)
        )
        self.window.present()

    def add_tray(self, tray) -> None:
        self.tray = tray

    @property
    def current_music(self):
        return self._music

    @property
    def pomodoro(self):
        return self._pomo

    @property
    def volume(self):
        return self._vol
